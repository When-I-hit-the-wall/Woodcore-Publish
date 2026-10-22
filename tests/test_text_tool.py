"""The Text tool of the four drawing engines, and the variable a text prints (calc/tools/text_pane.py, calc/domains/figure_text.py, spec docs/requirements/completed/2026-10-11-variables-liees-champs-et-textes.md, REQ-010, REQ-011, UI-004).

What is held, in each engine on a copy of the example project:

* **the tool** puts a text down where the click falls, selected, its pane on the right (REQ-010);
* **the pane**: the content typed is taken; «Insérer une variable» brings the «Variables» tab forward in its choosing mode, every number offered whatever its unit (D-08), and inserts the one chosen as a token; «valeur» / «symbole = valeur» changes what is printed (D-09); a brace alone is said and not taken (D-13);
* **saved and exported**, the source holds the token text, its variable and its last value at the version that says so; the export's record carries what the text printed, and the figure's SVG the printed words (REQ-010, REQ-011).

⚠️ Built off-screen; nothing here compiles Typst.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import sys

import conftest
import engine
from conftest import ROOT, Skip

import project

TOOLS = ROOT / "calc" / "tools"
_STATE = {}


def _window():
    if "window" not in _STATE:
        if str(TOOLS) not in sys.path:
            sys.path.insert(0, str(TOOLS))
        try:
            from PySide6.QtWidgets import QApplication
        except ImportError as exc:
            raise Skip(f"PySide6 is not installed ({exc})")
        QApplication.instance() or QApplication([])
        here = conftest.project_copy("text_tool")
        with project.using(here):
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            window.mode = "rs"
            window.apply_mode()
        _STATE.update(window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _listing(window):
    import variables_tab
    return next(t for t in window.tabs if isinstance(t, variables_tab.VariablesTab))


def _write_and_insert(window, tab, pane_of):
    """Types «Charge » into the pane of the text just placed, inserts snow-load/SL/L through «Variables», shows it as «symbole = valeur», and tries a brace alone. Returns the pane last built."""
    import variables_tab
    listing = _listing(window)
    pane = pane_of()
    pane.content.setPlainText("Charge ")
    assert pane.commit()
    pane.content.moveCursor(pane.content.textCursor().MoveOperation.End)
    pane.insert_button.click()
    assert window.tab_widget.currentWidget() is listing and not window.nav.isEnabled()
    snow = next(k for k, d in listing.domains.items() if k[0] == variables_tab.EXPORT and d.address == ("snow-load", "SL"))
    # D-08: a text takes any number, whatever its unit -- a length here, which no load field would take
    listing.select_key((*snow, "L"))
    listing.pick_chosen()
    assert window.tab_widget.currentWidget() is tab and window.nav.isEnabled()
    pane = pane_of()
    assert pane.entry["text"] == "Charge {1}" and pane.entry["vars"]["1"]["var"] == "L", pane.entry
    assert "17.5 m" in pane.prints.text()
    pane.cards[0]["show"].setCurrentIndex(1)
    assert pane.entry["vars"]["1"]["show"] == "symbol" and "L = 17.5 m" in pane.prints.text()
    # a brace alone is said and not taken
    pane.content.setPlainText("Charge {1} {")
    assert not pane.commit() and pane.refused and pane.entry["text"] == "Charge {1}"
    # a token naming no variable likewise
    pane.content.setPlainText("Charge {1} {9}")
    assert not pane.commit() and "{9}" in pane.refused and pane.entry["text"] == "Charge {1}"
    pane.content.setPlainText("Charge {1}")
    assert pane.commit()
    return pane


def test_a_text_is_placed_written_saved_and_exported_in_the_static_models():
    window, here = _window()
    import statics_tab
    from domains import statics
    with project.using(here):
        tab = next(t for t in window.tabs if isinstance(t, statics_tab.StaticsTab))
        window.tab_widget.setCurrentWidget(tab)
        source = statics.new_source("TX1")
        source.update(points=[{"id": "P1", "x": 0, "z": 0}, {"id": "P2", "x": 3, "z": 0}],
                      members=[{"id": "B1", "kind": "bar", "p1": "P1", "p2": "P2"}],
                      supports=[{"id": "A1", "point": "P1", "type": "pinned"}, {"id": "A2", "point": "P2", "type": "roller"}])
        tab.open_source(source, None, False)
        tab.choose_tool("text")
        tab.canvas.place((1.5, -1.0))
        collection, entry = tab.canvas.selected()
        assert collection == "texts" and entry["id"] == "T1" and (entry["x"], entry["z"]) == (1.5, -1)
        _write_and_insert(window, tab, lambda: tab.text_pane)

        assert tab.save()
        saved = json.loads((here.statics_dir / "TX1.json").read_text(encoding="utf-8"))
        assert saved["schema_version"] == statics.LINKED_SCHEMA_VERSION
        text = saved["texts"][0]
        assert text["text"] == "Charge {1}" and text["vars"]["1"]["last"] == {"value": 17.5, "unit": "m", "symbol": "L"}, text
        statics.check_source(saved, "TX1.json")
        exported = json.loads((here.data_dir / "statics.json").read_text(encoding="utf-8"))
        assert exported["models"]["TX1"]["texts"][0]["lines"] == ["Charge L = 17.5 m"]
        svg = engine.Figures(here.data_dir, "statics", here).path(engine.Figures(here.data_dir, "statics", here).name("TX1-de.svg")).read_text(encoding="utf-8")
        assert ">Charge L = 17.5 m<" in svg
        # its size, the selection's own `text` factor, and «Retirer», which takes the variable and its token
        tab.set_entry_style(entry, "text", 1.5)
        assert entry["style"] == {"text": 1.5}
        tab.text_pane.cards[0]["remove"].click()
        pane = tab.text_pane
        assert pane.entry["text"] == "Charge " and "vars" not in pane.entry and not pane.cards
        tab.dirty = False


def test_a_text_is_placed_written_saved_and_exported_in_the_schemas():
    window, here = _window()
    import schema_tab
    from domains import schema
    with project.using(here):
        tab = next(t for t in window.tabs if isinstance(t, schema_tab.SchemaTab))
        window.tab_widget.setCurrentWidget(tab)
        source = schema.new_source("TX1")
        source["connectors"] = [{"id": "C1", "kind": "Nagel", "x": 0, "z": 0}]
        tab.open_source(source, None, False)
        tab.choose_tool("text")
        tab.canvas.place((40.0, 25.0))
        collection, entry = tab.canvas.selected()
        assert collection == "texts" and entry["id"] == "T1" and (entry["x"], entry["z"]) == (40, 25)
        assert tab.text_pane is not None and tab.text_pane.entry is entry
        _write_and_insert(window, tab, lambda: tab.text_pane)

        assert tab.save()
        saved = json.loads((here.details_dir / "TX1.json").read_text(encoding="utf-8"))
        assert saved["schema_version"] == schema.TEXT_SCHEMA_VERSION and saved["texts"][0]["vars"]["1"]["last"]["value"] == 17.5
        schema.check_source(saved, "TX1.json")
        exported = json.loads((here.data_dir / "schemas.json").read_text(encoding="utf-8"))
        assert exported["schema_version"] == schema.SIZE_EXPORT_VERSION, "1.4 contains 1.3 and 1.2: every export since v0.120 (D7)"
        assert exported["schemas"]["TX1"]["texts"][0]["lines"] == ["Charge L = 17.5 m"]
        assert ">Charge L = 17.5 m<" in conftest.figure(here, exported["schemas"]["TX1"]["figures"]["de"]["file"]).read_text(encoding="utf-8")
        # the text deleted, the schema is 1.1 again
        tab.canvas.select(("texts", "T1"))
        tab.canvas.delete_selection()
        assert tab.save()
        saved = json.loads((here.details_dir / "TX1.json").read_text(encoding="utf-8"))
        assert saved["schema_version"] == schema.SOURCE_SCHEMA_VERSION and "texts" not in saved
        tab.dirty = False


def test_a_text_is_placed_written_saved_and_exported_in_a_position_plan():
    window, here = _window()
    import plan_tab
    from domains import plan
    with project.using(here):
        tab = next(t for t in window.tabs if type(t) is plan_tab.PlanTab)
        window.tab_widget.setCurrentWidget(tab)
        tab.load("Pavillon")
        crop = plan.crop_of(tab.source)
        at = (round(crop["x"] + crop["w"] / 2), round(crop["y"] + crop["h"] / 2))
        tab.choose_tool("text")
        tab.canvas._left_click(at, False)
        assert tab.canvas.selection[0] == "text" and tab.canvas.tool == "select"
        entry = tab.canvas._selected_of("text")
        assert entry["points"] == [list(at)] and tab.text_pane.entry is entry
        _write_and_insert(window, tab, lambda: tab.text_pane)
        # a click on the text takes it again
        tab.canvas.select(None)
        tab.canvas.press_select(at)
        assert tab.canvas.selection == ("text", 0)
        tab.canvas.drag = None

        said = []
        tab.fail = lambda text: said.append(text) or False
        assert tab.save(), said
        saved = json.loads((here.plans_dir / "Pavillon.json").read_text(encoding="utf-8"))
        assert saved["schema_version"] == plan.TEXT_SCHEMA_VERSION and saved["texts"][0]["vars"]["1"]["last"]["value"] == 17.5
        plan.check_source(saved, "Pavillon.json")
        # the plan's export, which a copy of the project cannot run whole (its backgrounds are not copied): the domain's, on a plan of its own
        _export_a_plan_with(saved["texts"])
        tab.dirty = False


def _export_a_plan_with(texts):
    """A blank plan carrying `texts`, exported: its record holds what they print, at 1.4, and its SVG the printed words; without them the plan is exported at 1.3 and its SVG has no text."""
    import tempfile
    from pathlib import Path
    from domains import links, plan
    values = links.index({"domains": {"snow-load": {"instances": {"SL": {"vars": {"L": {"value": 20, "unit": "m", "symbol": "L"}}}}}}})
    with tempfile.TemporaryDirectory(dir=conftest.TMP if conftest.TMP.is_dir() else None) as folder:
        root = Path(folder)
        (root / "plans").mkdir()
        source = plan.new_source("TX1")
        (root / "plans" / "TX1.json").write_text(json.dumps(source), encoding="utf-8")
        data, files, _notes = plan.prepare(root / "plans", root, root / "data", [], values)
        assert data["schema_version"] == plan.EXPORT_SCHEMA_VERSION and "texts" not in data["plans"]["TX1"]
        plain = files[data["plans"]["TX1"]["overlay"]]
        source["texts"] = texts
        source["schema_version"] = plan.version_of(source)
        (root / "plans" / "TX1.json").write_text(json.dumps(source), encoding="utf-8")
        data, files, _notes = plan.prepare(root / "plans", root, root / "data", [], values)
        assert data["schema_version"] == plan.TEXT_EXPORT_VERSION
        assert data["plans"]["TX1"]["texts"][0]["lines"] == ["Charge L = 20 m"], data["plans"]["TX1"]["texts"]
        svg = files[data["plans"]["TX1"]["overlay"]]
        assert ">Charge L = 20 m<" in svg and ">Charge" not in plain


def test_a_text_is_placed_written_saved_and_exported_in_a_fire_protection_plan():
    window, here = _window()
    import fire_tab
    from domains import fire, plan
    with project.using(here):
        tab = next(t for t in window.tabs if isinstance(t, fire_tab.FireTab))
        window.tab_widget.setCurrentWidget(tab)
        tab.load("Treppenhaus")
        crop = plan.crop_of(tab.canvas.frame_source())
        at = (round(crop["x"] + crop["w"] / 2), round(crop["y"] + crop["h"] / 2))
        tab.choose_tool("text")
        assert tab.canvas.tool == "text"
        tab.canvas.add_text(at)
        assert tab.canvas.selected == ["X1"] and tab.canvas.tool == "select", (tab.canvas.selected, tab.canvas.tool, tab.source.get("texts"))
        entry = tab.source["texts"][0]
        assert entry["points"] == [list(at)] and tab.text_pane is not None and tab.text_pane.entry is entry
        _write_and_insert(window, tab, lambda: tab.text_pane)
        # a click on the text takes it again, before what lies under it
        tab.canvas.select_ids([])
        tab.canvas.press_select(at, False)
        assert tab.canvas.selected == ["X1"]
        tab.canvas.drag = None

        said = []
        tab.fail = lambda text: said.append(text) or False
        assert tab.save(), said
        saved = json.loads((here.fire_dir / "Treppenhaus.json").read_text(encoding="utf-8"))
        assert saved["schema_version"] == fire.TEXT_SCHEMA_VERSION and saved["texts"][0]["id"] == "X1"
        assert saved["texts"][0]["vars"]["1"]["last"]["value"] == 17.5
        fire.check_source(saved, "Treppenhaus.json")
        exported = json.loads((here.data_dir / "fire.json").read_text(encoding="utf-8"))
        assert exported["schema_version"] == (fire.ROOTED_EXPORT_VERSION if here.has_folders else fire.TEXT_EXPORT_VERSION), "laid out by folders, 2.2 contains 2.1 (issue #64)"
        record = exported["plans"]["Treppenhaus"]
        assert record["texts"][0]["lines"] == ["Charge L = 17.5 m"] and record["texts"][0]["id"] == "X1"
        assert ">Charge L = 17.5 m<" in conftest.figure(here, record["figures"]["de"]).read_text(encoding="utf-8")
        # the plan turned with its page: the text with it
        turned = fire.rotate_source(saved, 1, (1000.0, 700.0))
        assert turned["texts"][0]["points"] == [[700 - at[1], at[0]]]
        # deleted, the plan is written as 2.0 again
        tab.canvas.select_ids(["X1"])
        tab.canvas.delete_selection()
        assert tab.save(), said
        saved = json.loads((here.fire_dir / "Treppenhaus.json").read_text(encoding="utf-8"))
        assert saved["schema_version"] == fire.SOURCE_SCHEMA_VERSION and "texts" not in saved
        tab.dirty = False
