"""What the engineer asked of the whole window at once, and what came with it (docs/ui/window.md §10quater):

- **Nom · Description · ID**, and nothing else of the kind, in every editor tab -- the ID composed of the name and writable over (calc/tools/identity.py);
- **a folder made is a folder kept**: until then four of the five editor tabs rebuilt their list from their own copy of the empty folders, taken before the new one was added, so a folder vanished the moment it was made; and a button for it at the right of each list's title;
- **a schema renamed is followed**: the connectors and the polar-moment calculations naming it are rewritten, and both tabs look at the schemas again when they are brought to the front;
- **the Connecteurs form lights one box at a time** -- the innermost under the pointer, with its frame drawn the same lit or not -- and a member's box lights its piece on the pattern.

Built off-screen; skipped where PySide6 is not installed.
"""

import json
import os
import re
import sys

from conftest import ROOT, Skip, tmpdir

_window = None


def _window_():
    global _window
    path = str(ROOT / "calc" / "tools")
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    QApplication.instance() or QApplication([])
    import woodcore_gui
    if _window is None:
        _window = woodcore_gui.MainWindow()
    for tab in _window.tabs:
        tab.dirty = False     # a dirty tab opens a modal on load, and a modal off-screen never returns
    return _window


def _tab(name):
    return next(t for t in _window_().tabs if type(t).__name__ == name)


def _row_labels(form):
    from PySide6.QtWidgets import QFormLayout, QLabel
    out = []
    for row in range(form.rowCount()):
        item = form.itemAt(row, QFormLayout.ItemRole.LabelRole)
        widget = item.widget() if item is not None else None
        if isinstance(widget, QLabel) and widget.text().strip():
            out.append(widget.text().strip().rstrip(":").strip())
    return out


# --- the ID a name composes -----------------------------------------------------------

def test_an_id_is_composed_of_the_name_with_accents_decomposed():
    _window_()
    import identity
    assert identity.slug_id("Velo Unterstand") == "Velo_Unterstand"
    assert identity.slug_id("Élément Café") == "Element_Cafe"
    assert identity.slug_id("  -Träger Süd ") == "Trager_Sud"
    assert identity.slug_id("") == ""


def test_a_new_object_s_id_follows_its_name_and_one_written_over_stays():
    _window_()
    import identity
    from PySide6.QtWidgets import QFormLayout, QWidget
    holder = QWidget()
    form = QFormLayout(holder)
    calls = []
    rows = identity.IdentityRows(form, lambda key: key, lambda: calls.append(1))
    rows.fill("", "", "D07", saved=False)
    rows.name.setText("Halle Nord")
    assert rows.id.text() == "Halle_Nord", "a new object's id follows its name from the first letter"
    rows.id.setText("H_N")
    rows.name.setText("Halle Süd")
    assert rows.id.text() == "H_N", "an id written over is the engineer's"
    assert calls, "every edit is reported"


def test_a_saved_object_is_not_renamed_by_giving_it_a_name():
    """Every object saved before names existed has an id that is not its name's slug: giving it a name must not rename its file behind the engineer's back."""
    _window_()
    import identity
    from PySide6.QtWidgets import QFormLayout, QWidget
    holder = QWidget()
    form = QFormLayout(holder)
    rows = identity.IdentityRows(form, lambda key: key, lambda: None)
    rows.fill("", "", "VU-Skizze", saved=True)
    rows.name.setText("Velo Unterstand")
    assert rows.id.text() == "VU-Skizze"


def test_every_editor_tab_names_its_objects_nom_description_id():
    window = _window_()
    t = window.t
    wanted = [t("idn_name"), t("idn_description"), t("idn_id")]
    for name in ("SchemaTab", "StaticsTab", "PlanTab"):
        tab = _tab(name)
        form = tab.identity.name.parentWidget().layout()
        labels = _row_labels(form)
        found = [label for label in labels if label in wanted]
        assert found == wanted, f"{name}: {labels}"
        assert not hasattr(tab, "group_edit"), f"{name}: the folder is set by dragging, not typed"


def test_the_connectors_identity_is_schema_name_description_id_and_nothing_else():
    window = _window_()
    tab = _tab("ConnectorsTab")
    form = tab.identity.name.parentWidget().layout()
    t = window.t
    labels = _row_labels(form)
    assert labels == [window.label("cn_schema").rstrip(":").strip(), t("idn_name"), t("idn_description"), t("idn_id")], labels
    for gone in ("group_edit", "variant_edit", "elements_edit", "length_box"):
        assert not hasattr(tab, gone), gone


def test_the_connector_s_description_takes_its_old_designation_and_its_members_are_read_off_the_schema():
    tab = _tab("ConnectorsTab")
    ids = tab._taken()
    if not ids:
        raise Skip("no connector saved in this project")
    tab.load(ids[0])
    source = json.loads((__import__("conftest").PROJECT.connectors_dir / f"{ids[0]}.json").read_text(encoding="utf-8"))
    assert tab.identity.description.text() == (source.get("description") or source.get("label", ""))
    draft = tab.draft()
    assert draft["label"] == ""
    assert draft["description"] == (source.get("description") or source.get("label", "")).strip()
    expected = [tab.element_position(m.get("element", "")) for m in draft["members"] if m.get("role") == "timber"]
    assert draft["elements"] == list(dict.fromkeys(p for p in expected if p))
    tab.dirty = False


# --- folders ---------------------------------------------------------------------------

def test_a_folder_made_in_any_editor_tab_is_still_there_after_the_list_is_rebuilt():
    """The defect the engineer met: «j'ai beau créer un nouveau dossier, je ne le vois pas apparaître»."""
    window = _window_()
    for name, key in (("SchemaTab", "tab_schema"), ("StaticsTab", "tab_statics"), ("PlanTab", "tab_plan"),
                      ("ConnectorsTab", "tab_connections"), ("PolarTab", "tab_polar")):
        tab = _tab(name)
        tab.list._ask = lambda *_args, **_kwargs: "Neu_77"
        try:
            tab.list.new_folder()
            folders = [tab.list.topLevelItem(i).text(0) for i in range(tab.list.topLevelItemCount())]
            assert "Neu_77" in folders, f"{name}: {folders}"
            assert "Neu_77" in tab.empty_folders, name
        finally:
            del tab.list._ask
            tab.list._empty = [n for n in tab.list._empty if n != "Neu_77"]
            tab.empty_folders = [n for n in tab.empty_folders if n != "Neu_77"]
            window.save_folder_settings(key, tab.empty_folders)


def test_every_list_carries_a_new_folder_button_at_the_right_of_its_title():
    from PySide6.QtWidgets import QToolButton
    for name in ("SchemaTab", "StaticsTab", "PlanTab", "ConnectorsTab", "PolarTab"):
        tab = _tab(name)
        row = tab.list.parentWidget()
        buttons = [b for b in row.findChildren(QToolButton) if getattr(b.parentWidget(), "new_folder_button", None) is b]
        assert len(buttons) == 1, name
        asked = []
        tab.list._ask = lambda *_args, **_kwargs: asked.append(1) or ""
        try:
            buttons[0].click()
        finally:
            del tab.list._ask
        assert asked, f"{name}: the button asks for a folder's name"


# --- a schema renamed ------------------------------------------------------------------

def test_a_schema_renamed_is_followed_by_the_connectors_and_calculations_naming_it():
    tab = _tab("SchemaTab")
    import schema_tab
    root = tmpdir("rename_references")
    connectors, connections = root / "connectors", root / "connections"
    connectors.mkdir()
    connections.mkdir()
    (connectors / "K1.json").write_text(json.dumps({"id": "K1", "schema": "Alt"}), encoding="utf-8")
    (connectors / "K2.json").write_text(json.dumps({"id": "K2", "schema": "Andere"}), encoding="utf-8")
    (connections / "M1.json").write_text(json.dumps({"id": "M1", "schema": "Alt"}), encoding="utf-8")
    import project
    scope = project.using(project.write(root / "Rename.woodcore", "Rename", {"sources": "."}))
    exports = []
    import domains.connector as connector_model
    import domains.connection as connection_model
    saved = connector_model.export, connection_model.export
    connector_model.export = lambda *args, **kwargs: exports.append("connectors")
    connection_model.export = lambda *args, **kwargs: exports.append("connections")
    scope.__enter__()
    followed = []
    others = [t for t in tab.app.tabs if hasattr(t, "schema_renamed")]
    originals = {t: t.schema_renamed for t in others}
    for other in others:
        other.schema_renamed = lambda old, new, who=type(other).__name__: followed.append((who, old, new))
    try:
        names = tab.rename_references("Alt", "Neu")
    finally:
        scope.__exit__(None, None, None)
        connector_model.export, connection_model.export = saved
        for other, method in originals.items():
            other.schema_renamed = method
    assert sorted(names) == ["K1", "M1"]
    assert json.loads((connectors / "K1.json").read_text(encoding="utf-8"))["schema"] == "Neu"
    assert json.loads((connectors / "K2.json").read_text(encoding="utf-8"))["schema"] == "Andere"
    assert json.loads((connections / "M1.json").read_text(encoding="utf-8"))["schema"] == "Neu"
    assert sorted(exports) == ["connections", "connectors"]
    assert {who for who, _old, _new in followed} == {"ConnectorsTab", "PolarTab"}


def test_bringing_a_tab_to_the_front_reads_the_schemas_again():
    window = _window_()
    for name in ("ConnectorsTab", "PolarTab"):
        tab = _tab(name)
        seen = []
        original = tab.on_shown
        tab.on_shown = lambda: seen.append(1)
        try:
            window.tab_widget.setCurrentWidget(_tab("SchemaTab"))
            window.tab_widget.setCurrentWidget(tab)
        finally:
            tab.on_shown = original
        assert seen, name
        tab.on_shown()          # and doing it for real keeps the form usable
        tab.dirty = False


# --- the Connecteurs form's boxes -----------------------------------------------------

def test_a_member_s_box_alone_is_lit_and_its_piece_is_lit_on_the_pattern():
    tab = _tab("ConnectorsTab")
    ids = tab._taken()
    if not ids:
        raise Skip("no connector saved in this project")
    tab.load(ids[0])
    members = [box for box, index in tab.member_boxes.items() if index == 1]
    if not members:
        raise Skip("this connector has one member")
    box = members[0]
    tab.set_hot(box)
    lit = [b for b in tab.box_results if b.property("hot")]
    assert lit == [box], [b.title() for b in lit]
    element = tab.member_fields[1]["element"].currentData() or ""
    assert tab.marked() == (("elements", element) if element else None)
    tab.set_hot(None)
    assert not [b for b in tab.box_results if b.property("hot")]
    tab.dirty = False


def test_a_box_lit_and_a_box_not_share_one_style_sheet():
    """The frames jumped because a lit box took a style sheet and an unlit one the native frame; one style sheet with a `hot` property changes the colour and nothing else -- the window's own since v0.90 (theme.py), where it was the tab's."""
    tab = _tab("ConnectorsTab")
    import theme
    assert 'QGroupBox[hot="true"]' in theme.STYLE and "{lit_line}" in theme.STYLE
    box = next(iter(tab.box_results))
    before = box.contentsRect()
    tab.set_hot(box)
    assert box.contentsRect() == before
    tab.set_hot(None)
    assert box.styleSheet() == "", "no box carries a sheet of its own any more"


def test_the_pattern_lights_an_element_and_a_marker_it_is_handed():
    _window_()
    from domains import connector_svg, schema_svg
    detail = {"id": "S", "elements": [{"id": "E1", "kind": "linear", "points": [[0, 0], [300, 0]], "h": 100}],
              "connectors": [{"id": "C1", "kind": "Stabdübel", "x": 100, "z": 0}, {"id": "C2", "kind": "Stabdübel", "x": 200, "z": 0}],
              "aids": [], "dimensions": []}
    source = {"fasteners": ["C1", "C2"], "diameter": {"value": 12}}
    plain = connector_svg.pattern_of(source, detail)
    lit = connector_svg.pattern_of(source, detail, highlight=("elements", "E1"))
    assert schema_svg.HIGHLIGHT not in plain
    assert schema_svg.HIGHLIGHT in lit, "a chosen element was handed over as a fastener index, and never lit"
    marker = connector_svg.pattern_of(source, detail, highlight=("connectors", "C2"))
    assert marker != plain and len(re.findall(r'r="[\d.]+" fill="none" stroke="', marker)) >= 1
