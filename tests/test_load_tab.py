"""The tabs of loads entered in Woodcore (issues #35-#37, spec docs/requirements/completed/2026-10-10-issues-github-35-a-39.md; on the type «Calcul» since issues #95 and #100 -- calc/tools/dead_load_tab.py, snow_tab.py, wind_tab.py, whose own tests are tests/test_calc_tab_base.py and tests/test_wind_tab.py).

What is held: «Poids propre et surcharge» is one tab (D-08) that lists its build-ups, edits the layers in a table at the keyboard -- each g_k or a_k, a material, a thickness, pieces at a spacing, a line linked with the one below that fills between them (issue #111) --, shows at once the sums, «Couche n», the section and the contributions, saves the source at dead-load-source 2.0 and exports calculations.json with the case under the domain dead-load (UI-001 to UI-004, REQ-002); every build-up at a glance; a build-up made from a template, one kept as a template.

⚠️ Built off-screen; nothing here opens a dialog.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import os
import sys

import conftest
from conftest import ROOT

import project

TOOLS = ROOT / "calc" / "tools"
_STATE = {}


def _qt():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise conftest.Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _window():
    if "window" not in _STATE:
        _qt()
        here = conftest.project_copy("load_tab")
        with project.using(here):
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            window.mode = "rs"
            window.apply_mode()
        _STATE.update(window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(window, key):
    return next(t for t in window.tabs if getattr(t, "KEY", None) == key)


def _select(combo, data):
    index = combo.findData(data)
    assert index >= 0, (data, [combo.itemData(i) for i in range(combo.count())])
    combo.setCurrentIndex(index)


def _value(cell, value):
    """A number typed into a cell of the table of layers (its spin, behind its button of variable)."""
    getattr(cell, "spin", cell).setValue(value)


def test_the_dead_load_tab_edits_layers_shows_the_sums_and_the_drawing_and_saves_and_exports():
    window, here = _window()
    with project.using(here):
        import calc_tab
        import dead_load_tab
        from domains import dead_load_source, materials_catalogue
        tab = _tab(window, "tab_ac_selfweight")
        assert isinstance(tab, dead_load_tab.DeadLoadTab) and isinstance(tab, calc_tab.CalcTab)   # on the type «Calcul» since issue #95 (REQ-003)
        layers, modules = tab.service("layers"), tab.service("modules")
        assert not tab.has_service("materials"), "the tab creates no material any more (issue #110, REQ-016)"
        assert "ProjectMaterials" not in [s.__name__ for s in dead_load_tab.DeadLoadTab.SERVICES]
        tab.dirty = False
        tab.new()
        tab.service("identity").rows.id.setText("AU-31")
        tab.service("identity").rows.name.setText("Flachdach Test")
        assert layers.table.rowCount() == 1 and layers.layers[0]["pose"] == "continuous"
        layers.add_layer()
        layers.add_layer()
        assert layers.table.rowCount() == 3 and layers.open == 2, "+ Couche: a line, the cursor in its material (T52)"
        # layer 2: rafters 60/200 at 625, spaced, linked with layer 3 below them: the insulation that fills between them
        c24, flumroc = materials_catalogue.ext_id("C24", "Konstruktion"), materials_catalogue.ext_id("Flumroc Typ 1", "Dämmung")
        combo = layers.cell(1, "material")
        combo.setCurrentIndex(combo.index_of(c24))
        layers.open_row(1)
        layers.option_changed("pose", "spaced")
        assert layers.layers[1]["pose"] == "spaced" and layers.cell(1, "spacing").isEnabled() and not layers.cell(0, "spacing").isEnabled(), "a cell that does not serve greyed (T50)"
        _value(layers.cell(1, "thickness"), 200)
        _value(layers.cell(1, "spacing"), 625)
        _value(layers.cell(1, "width"), 60)
        combo = layers.cell(2, "material")
        combo.search("flumroc 1")
        assert combo.index_of(flumroc) >= 0 and combo.index_of("sia265:C24") < 0, "the domain's search"
        combo.setCurrentIndex(combo.index_of(flumroc))
        _value(layers.cell(2, "thickness"), 200)
        layers.open_row(1)
        layers.option_changed("link", True)
        assert layers.layers[1]["link"] and layers.table.rowCount() == 3
        assert tab.instance is not None, tab.ctx.messages
        assert round(layers.shown[2]["fill_width"]) == 904 and layers.cell(2, "width").spin.font().italic(), "the width the wool fills, computed, in italics (T51)"
        sums = tab.instance["vars"]
        gk_before, ak_before = sums["gk"]["value"], sums["ak"]["value"]
        assert gk_before > 0 and ak_before == 0
        assert modules.pane.ids()[:4] == ["state", "layer", "drawing", "results"], "the right pane in its order (UI-002)"
        assert "60" in tab.ctx.drawing and tab.ctx.drawing == tab.instance["_files"][next(iter(tab.instance["_files"]))], "the tab's drawing is the export's"
        # REQ-002: the insulation moved to a_k
        _select(layers.cell(2, "kind"), "ak")
        assert tab.instance["vars"]["ak"]["value"] > 0 and tab.instance["vars"]["gk"]["value"] < gk_before
        results = modules.pane.modules["results"].body.text()
        assert "g<sub>k</sub>" in results and "<table" in results, "the values, then the table of the layers (REQ-003)"
        assert tab.save(), tab.ctx.reason
        cid = tab.current_id
        source = json.loads((here.sources_dir / dead_load_source.FOLDER / ("%s.json" % cid)).read_text(encoding="utf-8"))
        assert [l["kind"] for l in source["layers"]] == ["gk", "gk", "ak"] and source["layers"][1]["link"] is True and source["layers"][2]["fill"] is True
        assert source["layers"][1]["spacing"] == 625 and source["name"] == "Flachdach Test"
        assert source["schema_version"] == "2.0" and source["layers"][2]["material"] == flumroc and source["layers"][1]["pose"] == "spaced"
        exported = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        instance = exported["domains"]["dead-load"]["instances"][cid]
        assert instance["source_file"] == "loads/dead/%s.json" % cid and instance["figures"]
        assert conftest.figure(here, instance["figures"][0]["file"]).is_file()
        import display_view
        assert display_view.entry_call(tab.display_entries()[0]) == '#include domain-file("dead-load", "%s")' % cid
        # a material of the engineer's own (the «Matériaux» tab's), offered at once, and its copy taken by the project at the save (REQ-013)
        from domains import materials, materials_user
        mine = materials_user.blank("other", "board")
        mine["names"]["fr"] = "Hersteller OSB"
        mine["weight"] = {"value": 6.2, "unit": "kN/m³", "ref": "Datenblatt"}
        mine["source"] = {"kind": "url", "url": "https://example.org"}
        materials_user.save(mine)
        layers.rebuild()
        combo = layers.cell(0, "material")
        combo.setCurrentIndex(combo.index_of(mine["id"]))
        assert combo.currentIndex() >= 0 and layers.layers[0]["material"] == mine["id"]
        assert tab.save(), tab.ctx.reason
        kept = materials.read_project(here)
        assert kept["schema_version"] == "2.0" and [m["id"] for m in kept["materials"]] == [mine["id"]]
        assert not tab.service("material_copies").box.isVisibleTo(tab)
        materials_user.save(dict(mine, weight={"value": 6.5, "unit": "kN/m³", "ref": "Datenblatt"}))
        tab.ctx.refresh()
        copies = tab.service("material_copies")
        assert [w["kind"] for w in copies.said] == ["changed"] and any(m.code == "material_changed" for m in tab.ctx.messages), "the library changed: said (REQ-014)"
        assert copies.keep_material(mine["id"]) and copies.said == []
        materials_user.delete(mine["id"])
        tab.dirty = False


def test_the_table_of_layers_at_the_keyboard_and_its_line_open():
    """UI-001, UI-002 (T23, T26, T28, T29, T48 to T52): Tab from the material to the thickness, the spacing, the width, g/a and the kN/m², the cells a pose does not use skipped, after the last the next line's material; a message clicked opens its line; «Lier» on the last line makes the next one; a load typed in the kN/m² replaces the calculation, in orange, «Rétablir» takes it back; «+ Charge saisie» says in red that it has no value until one is typed; Escape closes the line."""
    window, here = _window()
    with project.using(here):
        import layer_cells
        import theme
        tab = _tab(window, "tab_ac_selfweight")
        layers = tab.service("layers")
        tab.dirty = False
        tab.new()
        layers.add_layer()
        combo = layers.cell(1, "material")
        combo.setCurrentIndex(combo.index_of("ext:93"))
        layers.open_row(1)
        layers.option_changed("pose", "spaced")
        chain, at = [], (0, "material")
        while at is not None:
            chain.append(at)
            at = layer_cells.next_cell(layers.layers, at[0], at[1], True)
        assert chain == [(0, "material"), (0, "thickness"), (0, "kind"), (0, "load"),
                         (1, "material"), (1, "thickness"), (1, "spacing"), (1, "width"), (1, "kind"), (1, "load")], chain
        assert layer_cells.next_cell(layers.layers, 1, "material", False) == (0, "load"), "Shift+Tab goes back to the line above"
        layers.tab_from((0, "load"), True)
        assert layers.open == 1 and layers.table.currentColumn() == layer_cells.COLUMNS.index("material")
        # a message about a line, clicked: the line opened
        tab.ctx.focus_field("layers[0]")
        assert layers.open == 0
        layers.close_row()
        assert layers.open is None
        # a load typed replaces the calculation, orange; «Rétablir» takes it back
        for key, value in (("thickness", 200), ("spacing", 625), ("width", 60)):
            _value(layers.cell(1, key), value)
        assert not any(m.severity == "error" for m in tab.ctx.messages), tab.ctx.messages
        layers.open_row(0)
        layers.option_changed("load", 0.2)
        assert layers.layers[0]["load"] == 0.2 and theme.colour("warning") in layers.cell(0, "load").spin.styleSheet()
        assert any(m.code == "load_replaced" and m.severity == "warning" for m in tab.ctx.messages)
        layers.option_changed("load", None)
        assert layers.layers[0]["load"] is None and not any(m.code == "load_replaced" for m in tab.ctx.messages)
        # «Lier» on the last line makes the next one, the cursor in its material (T29)
        layers.open_row(1)
        layers.option_changed("link", True)
        assert layers.table.rowCount() == 3 and layers.open == 2 and layers.layers[1]["link"]
        assert any(m.code == "no_material" and m.field == "layers[2]" for m in tab.ctx.messages), "a line with no material, said in red"
        layers.remove_layer()
        layers.open_row(1)
        layers.option_changed("link", False)
        # «+ Charge saisie»: red until its value is typed
        layers.add_typed()
        assert layers.layers[-1]["pose"] == "typed" and not layers.cell(len(layers.layers) - 1, "thickness").isEnabled()
        assert any(m.code == "missing_load" for m in tab.ctx.messages)
        _value(layers.cell(len(layers.layers) - 1, "load"), 0.5)
        assert not any(m.severity == "error" for m in tab.ctx.messages), tab.ctx.messages
        tab.dirty = False


def test_the_section_the_contributions_the_overview_and_the_templates():
    """UI-002 to UI-004, REQ-008 to REQ-011 (T44 to T46, T55, T57, T58): the section drawn at its module's width, a click on a layer opening its line; the contributions; «⊞ Vue d'ensemble» shown in the centre with a line per saved build-up, a line clicked opening its case; «Nouveau» from a Lignum template makes a build-up of the project; «Enregistrer comme modèle» keeps it in «Mes modèles»."""
    window, here = _window()
    with project.using(here):
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtTest import QTest
        from domains import dead_load_source
        tab = _tab(window, "tab_ac_selfweight")
        layers, modules = tab.service("layers"), tab.service("modules")
        tab.dirty = False
        shipped, _mine, _problems = dead_load_source.templates()
        sand = next(t for t in shipped if t["id"] == "lignum-c7-abb13-2")
        tab.service("templates").choose(sand)
        assert [l["material"] for l in layers.layers] == [l["material"] for l in sand["layers"]] and tab.source["name"] == dead_load_source.template_name(sand, window.lang)
        assert tab.instance is not None and round(tab.instance["vars"]["gk_ak"]["value"], 3) == 1.258
        body = modules.pane.modules["drawing"].body
        body.resize(600, 300)
        body.refresh()
        assert body.boxes, "the section drawn, its boxes to click"
        number, x, y, w, h = next(b for b in body.boxes if b[0] == 4)
        scale = body.section.width() / body.section.renderer().defaultSize().width()
        QTest.mouseClick(body.section, Qt.MouseButton.LeftButton, pos=QPoint(round((x + w / 2) * scale), round((y + h / 2) * scale)))
        assert layers.open == 3, "a click on the sand opens its line (UI-003)"
        assert "g_k + a_k" in body.lists.text() and "%" in body.lists.text()
        assert tab.save(), tab.ctx.reason
        cid = tab.current_id
        # «Mes modèles»
        kept = layers.save_as_template("Plancher sable, mon modèle")
        _shipped, mine, _problems = dead_load_source.templates()
        assert kept and [t["id"] for t in mine] == [kept["id"]]
        dead_load_source.delete_template(kept["id"])
        # the overview: shown in the centre, a line per build-up, a line clicked opens its case
        overview = tab.service("overview")
        overview.show(True)
        assert tab.ctx.overview and overview.button.isChecked()
        ids = [overview.table.item(r, 1).text() for r in range(overview.table.rowCount())]
        assert cid in ids and len(ids) == len(tab.ctx.store.ids())
        overview.open_line(ids.index(cid), 1)
        assert not tab.ctx.overview and tab.current_id == cid
        tab.dirty = False


def test_a_build_up_following_another_that_follows_it_is_refused_and_a_replaced_load_carries_no_mark():
    """REQ-006, ARCH-005: a layer's load following the retained value of another build-up that follows this one closes a circle, refused as it is chosen; the file of a build-up whose load is replaced prints the value alone, without a mark; a table masked in «Affichage» is commented out in the file (REQ-013, UI-005)."""
    window, here = _window()
    with project.using(here):
        from domains import dead_load_source, links, unfold, unfold_display
        tab = _tab(window, "tab_ac_selfweight")
        layers = tab.service("layers")
        tab.dirty = False
        tab.new()
        tab.service("identity").rows.id.setText("AU-81")
        layers.open_row(0)
        layers.option_changed("load", 0.25)
        assert tab.save(), tab.ctx.reason
        text = unfold.domain_path(here, "AU-81", kind="dead-load").read_text(encoding="utf-8")
        table = next(l for l in text.splitlines() if "#table(" in l)
        assert "[5 kN/m³], [0.25]," in table and "orange" not in table and "remplac" not in table.lower(), "the layer's row prints the value alone, as any other (the totals bold, as always)"
        # a second build-up whose chosen value follows AU-81: AU-81's load following it back closes a circle
        other = dead_load_source.new_source("AU-82")
        other["links"] = {"chosen": links.make("dead-load", "AU-81", "gk_ak_gew")}
        folder = here.sources_dir / dead_load_source.FOLDER
        (folder / "AU-82.json").write_text(json.dumps(dead_load_source.stamp_version(other), indent=2), encoding="utf-8")
        try:
            message = tab.ctx.links.refuse(links.make("dead-load", "AU-82", "gk_ak_gew"))
            assert message and "AU-82" in message and "AU-81" in message, message
            assert tab.ctx.links.refuse(links.make("dead-load", "AU-99", "gk_ak_gew")) is None
        finally:
            (folder / "AU-82.json").unlink()
        # «Affichage»: the table of the layers masked, its line commented out
        unfold_display.set_table(here, "AU-81", 1, "dead-load", shown=False)
        text = unfold.domain_path(here, "AU-81", kind="dead-load").read_text(encoding="utf-8")
        assert next(l for l in text.splitlines() if "#table(" in l).lstrip().startswith("//"), "masked: commented out, never printed"
        tab.dirty = False


def test_the_snow_tab_is_drawn_from_its_declaration_computes_at_once_and_saves():
    """UI-004 (issue #36), rebuilt on the calculation tabs' base (spec 2026-10-22-onglet-neige-type, ARCH-002, REQ-005, REQ-007): the building first and always, the site, the roof among five tiles -- its slopes shown for its form alone --, the sliding; the loads at once; saved and exported under snow-load, the building's length and width kept whatever the roof."""
    window, here = _window()
    with project.using(here):
        import calc_tab
        import snow_tab
        from domains import snow_source
        tab = _tab(window, "tab_ac_snow")
        assert isinstance(tab, snow_tab.SnowTab) and isinstance(tab, calc_tab.CalcTab)
        tab.dirty = False
        tab.new()
        f = tab.service("form").fields    # the widgets are the services' (spec 2026-10-23-onglets-types-et-services, REQ-001)

        def shown(key):
            form, widget = tab.service("form").rows[key]
            return form.isRowVisible(widget)
        f["h_0"].spin.setValue(638)
        f["roof"].buttons["curved"].click()
        assert shown("alpha_1") and not shown("alpha_2") and shown("length") and shown("width"), "the building is always entered (T37)"
        f["alpha_1"].spin.setValue(10)
        assert tab.instance and tab.instance["results"] == ["q_k1", "q_k3", "q_k3h"], tab.ctx.messages
        # a gable roof: both pitches shown, model 1 on each slope and model 2's halves
        f["roof"].buttons["duo"].click()
        assert shown("alpha_1") and shown("alpha_2")
        f["alpha_1"].spin.setValue(20)
        f["alpha_2"].spin.setValue(40)
        v = tab.instance["vars"]
        assert tab.instance["results"] == ["q_k11", "q_k12", "q_k11h", "q_k12h"], tab.ctx.messages
        assert v["q_k11"]["value"] > v["q_k12"]["value"] > 0, "the steeper slope carries less (Figur 2)"
        f["roof"].buttons["flat"].click()
        assert not shown("alpha_1") and shown("length")
        f["length"].spin.setValue(24)
        f["width"].spin.setValue(22)
        assert abs(tab.instance["vars"]["mu_1"]["value"] - 0.96) < 1e-12
        assert [m.code for m in tab.ctx.messages] == ["large_flat"], tab.ctx.messages
        assert tab.save(), tab.ctx.messages
        cid = tab.current_id
        source = json.loads((here.sources_dir / snow_source.FOLDER / ("%s.json" % cid)).read_text(encoding="utf-8"))
        assert source["roof"] == "flat" and source["length"] == 24 and source["width"] == 22 and source["schema_version"] == "1.0"
        exported = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        instance = exported["domains"]["snow-load"]["instances"][cid]
        assert instance["source_file"] == "loads/snow/%s.json" % cid and instance["figures"][0]["file"].endswith("%s-fig3.svg" % cid)
        tab.dirty = False


def test_a_free_c_e_is_written_at_1_3_and_said_by_no_message():
    """REQ-006, REQ-021, D-10: the three buttons of C_e say what they are worth, and a value typed beside them is the case's C_e -- no message, the source written at 1.3."""
    window, here = _window()
    with project.using(here):
        from domains import snow_source
        tab = _tab(window, "tab_ac_snow")
        tab.dirty = False
        tab.new()
        exposure = tab.service("form").fields["exposure"]
        assert [b.text() for b in exposure.buttons.values()] == [tab.t("sn_c_exposure_" + w) + " " + n for w, n in (("sheltered", "1.2"), ("normal", "1"), ("exposed", "0.8"))]   # «abrité 1.2» (T38)
        exposure.free.setValue(0.95)
        assert tab.draft()["exposure"] == "custom" and tab.draft()["c_e"] == 0.95
        assert tab.instance["vars"]["ce"]["value"] == 0.95 and not [m for m in tab.ctx.messages if m.field in ("exposure", "c_e")]
        assert tab.save()
        source = json.loads((here.sources_dir / snow_source.FOLDER / ("%s.json" % tab.current_id)).read_text(encoding="utf-8"))
        assert source["schema_version"] == "1.3" and source["c_e"] == 0.95
        exposure.buttons["sheltered"].click()
        assert tab.draft()["exposure"] == "sheltered" and "c_e" not in tab.draft()
        tab.dirty = False


def test_the_wind_tab_offers_every_building_table_computes_at_once_and_saves():
    """UI-005 (issue #37; on the type «Calcul» since issue #100): q_p0, the terrain, b, d, h, z, the table of Annexe C -- all 37 buildings offered (D-06) --, c_d; q_p and the forces at once, their tables shown; saved and exported under wind-load."""
    window, here = _window()
    with project.using(here):
        import calc_tab
        import wind_tab
        from domains import wind_source
        from norms import sia261_wind
        tab = _tab(window, "tab_ac_wind")
        assert isinstance(tab, wind_tab.WindTab) and isinstance(tab, calc_tab.CalcTab)
        form = tab.service("form")
        table = form.fields["table"].combo
        assert [table.itemData(i) for i in range(table.count())] == list(sia261_wind.NUMBERS)
        tab.dirty = False
        tab.new()
        _select(table, "45")
        form.fields["h"].spin.setValue(9)
        assert tab.instance and tab.instance["vars"]["qp"]["value"] > 0, tab.reason
        assert "qk_max_cf1" in tab.instance["vars"] and tab.service("modules").pane.modules["results"].body.blocks, "the global forces and the local pressures at their φ under the values (D-34)"
        assert tab.save(), tab.reason
        cid = tab.current_id
        source = json.loads((here.sources_dir / wind_source.FOLDER / ("%s.json" % cid)).read_text(encoding="utf-8"))
        assert source["table"] == "45" and source["h"] == 9 and source["z"] is None
        exported = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        assert exported["domains"]["wind-load"]["instances"][cid]["source_file"] == "loads/wind/%s.json" % cid
        tab.dirty = False


def test_the_snow_tabs_state_says_red_orange_and_green_and_a_click_takes_to_the_field():
    """REQ-008 (D-19): above 2000 m an orange message, the calculation made -- its words without «calculé quand même» --; above 800 m the cornice; a C_T of 0 a red one naming its field, no result; every input there, the green line. A click on a message gives its field the focus and makes it flash."""
    window, here = _window()
    with project.using(here):
        from norms import sia261_snow
        tab = _tab(window, "tab_ac_snow")
        tab.dirty = False
        tab.new()
        state = tab.service("modules").pane.modules["state"].body
        fields = tab.service("form").fields
        fields["h_0"].spin.setValue(700)
        assert tab.instance and [r.text() for r in state.rows] == ["✓ " + tab.t("ct_complete")]
        fields["h_0"].spin.setValue(2100)
        assert tab.instance and tab.instance["vars"]["h_0"]["value"] == 2100
        limit = sia261_snow.clause()["max_altitude"]
        said = tab.t("sn_msg_above_limit", h_0="2100", limit="%g" % limit["value"], ref=limit["norm_ref"])
        assert [r.text() for r in state.rows] == ["✓ " + tab.t("ct_complete"), said] and state.rows[1].property("callout") == "warning"
        fields["h_0"].spin.setValue(850)
        assert "5.3.7" in state.rows[1].text()
        fields["c_t"].spin.setValue(0)
        assert tab.instance is None and state.rows[0].property("callout") == "danger" and [m.field for m in tab.ctx.messages if m.severity == "error"] == ["c_t"]
        state.rows[0].mousePressEvent(None)
        assert fields["c_t"].blinking
        assert "<svg" in (tab.ctx.drawing or "<svg"), "the drawing of a case that cannot be computed is the last one's or none"
        fields["c_t"].spin.setValue(1)
        assert tab.instance and "<svg" in tab.ctx.drawing
        tab.dirty = False


def test_supprimer_archives_the_case_and_leaves_no_draft_that_saves_itself():
    """Issue #97: a snow case deleted is listed under «Archives», and what the form shows next is a draft nobody asked for -- no dot, never saved by itself: the draft «Nouveau» opened with its dot was saved without a word as soon as the engineer looked elsewhere (`SN-01.json`, empty), and «Supprimer» on it opened another one, so the tab could never be emptied."""
    window, here = _window()
    from PySide6.QtWidgets import QMessageBox
    import autosave
    original = QMessageBox.__dict__["question"]
    QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
    try:
        with project.using(here):
            from domains import snow_source
            tab = _tab(window, "tab_ac_snow")
            folder = here.sources_dir / snow_source.FOLDER
            tab.dirty = False
            tab.new()
            tab.service("identity").rows.id.setText("Neige_97")
            assert tab.save(), tab.ctx.messages
            before = sorted(p.name for p in folder.glob("*.json"))
            tab.service("cases").list.select("Neige_97")
            tab.delete()
            assert not (folder / "Neige_97.json").exists()
            archived = [e for e in tab.service("cases").list.archived_ids() if e.endswith("-Neige_97.json")]
            assert archived, ("the case deleted is not listed under «Archives»", tab.service("cases").list.archived_ids())
            assert tab.current_id is None and not tab.dirty, "the form after «Supprimer» holds a draft marked unsaved"
            assert autosave.leave(window, tab, "replace") and autosave.leave(window, tab, "close")
            assert sorted(p.name for p in folder.glob("*.json")) == [n for n in before if n != "Neige_97.json"], "a draft nobody asked for was saved"
            tab.delete()    # «Supprimer» on that draft: nothing saved, nothing archived, still no dot
            assert not tab.dirty and sorted(p.name for p in folder.glob("*.json")) == [n for n in before if n != "Neige_97.json"]
    finally:
        QMessageBox.question = original
        tab.dirty = False


def test_the_load_tab_words_exist_in_the_three_languages():
    """ARCH-RISK-004 of spec 2026-10-14-neige-vent-affichage-altitude: tests/test_i18n.py does not read load_tab.STRINGS, so the three languages are held equal here -- the snow's own since the spec 2026-10-22-onglet-neige-type (snow_tab_words, calc_tab_words), the 2000 m read from the norm file and said without «calculé quand même» (T50)."""
    _qt()
    import calc_tab_words
    import load_words
    import snow_tab_words
    import wind_tab_words
    for module in (load_words, calc_tab_words, snow_tab_words, wind_tab_words):
        assert set(module.STRINGS["fr"]) == set(module.STRINGS["de"]) == set(module.STRINGS["en"]), module.__name__
    for lang in ("fr", "de", "en"):
        text = snow_tab_words.STRINGS[lang]["sn_msg_above_limit"]
        assert "{h_0}" in text and "{limit}" in text and "{ref}" in text and "2000" not in text
        assert "quand même" not in text and "trotzdem" not in text and "all the same" not in text


def test_the_snow_s_save_is_refused_read_only_and_followed_by_the_domains_files_once():
    """ARCH-004 of the spec 2026-10-23-onglets-types-et-services: «Enregistrer» of the snow, on its type, refuses a project open read-only before it asks anything and writes nothing; saved, the domains' files are reconciled once -- by its store's guarded writer, not by the tab's too."""
    window, here = _window()
    import tab_guard
    with project.using(here):
        from domains import snow_source
        tab = _tab(window, "tab_ac_snow")
        folder = here.sources_dir / snow_source.FOLDER
        tab.dirty = False
        tab.new()
        tab.service("identity").rows.id.setText("Neige_RO")
        refused, synced = [], []
        original_refuse, original_sync = window.refuse_read_only, tab_guard._sync_domains
        window.refuse_read_only = lambda: refused.append(1)
        tab_guard._sync_domains = lambda app: synced.append(app)
        try:
            window.read_only = True
            assert tab.save() is False and refused == [1] and not (folder / "Neige_RO.json").exists(), "refused once, nothing written"
            window.read_only = False
            assert tab.save() and (folder / "Neige_RO.json").exists()
            assert synced == [window], "the domains' files reconciled once after the save"
        finally:
            window.read_only = False
            window.refuse_read_only, tab_guard._sync_domains = original_refuse, original_sync
            tab.dirty = False


def test_the_wind_s_save_is_refused_read_only():
    """ARCH-004 of the spec 2026-10-23-onglets-types-et-services: the wind's «Enregistrer», on its type since issue #100 -- the store's rules (source_store) --, refused in a project open read-only before it asks anything."""
    window, here = _window()
    with project.using(here):
        from domains import wind_source
        tab = _tab(window, "tab_ac_wind")
        tab.dirty = False
        tab.new()
        tab.service("identity").rows.id.setText("Wind_RO")
        refused, original = [], window.refuse_read_only
        window.refuse_read_only = lambda: refused.append(1)
        try:
            window.read_only = True
            assert tab.save() is False and refused == [1]
            assert not (here.sources_dir / wind_source.FOLDER / "Wind_RO.json").exists()
        finally:
            window.read_only = False
            window.refuse_read_only = original
            tab.dirty = False


def test_the_permanent_load_s_file_follows_its_case_without_a_question():
    """D-21 of the spec 2026-10-23-onglets-types-et-services: on the type «Calcul», the file of a case of permanent loads follows its case as the snow's does -- a value changed (a layer added) refreshes its lines in place, a change made by hand in a line kept; the retained value is always in the file since issue #111 (REQ-005, P01), so a value written in its place is a value refreshed, the form the same (the form changed and written again, never asked: the wind's, test_unfold); it then matches its case."""
    window, here = _window()
    with project.using(here):
        from domains import unfold
        tab = _tab(window, "tab_ac_selfweight")
        layers = tab.service("layers")
        tab.dirty = False
        tab.new()
        tab.service("identity").rows.id.setText("AU-95")
        assert tab.save(), tab.ctx.reason
        path = unfold.domain_path(here, "AU-95", kind="dead-load")
        assert path.is_file(), path
        before = path.read_text(encoding="utf-8")
        touched = next(l for l in before.splitlines() if '#var("gk"' in l)
        assert 'label: "Eigengewicht (Flächenlast)"' in touched, touched
        assert '"gk_ak_gew"' in before, "the retained value, written or the tenth above the sum, always there (issue #111, REQ-005)"
        path.write_text(before.replace(touched, touched.replace('label: "Eigengewicht (Flächenlast)"', 'label: "retouche à la main"')), encoding="utf-8", newline="\n")
        layers.add_layer()
        combo = layers.cell(1, "material")
        combo.setCurrentIndex(combo.index_of("ext:93"))
        _value(layers.cell(1, "thickness"), 80)
        assert tab.save(), tab.ctx.reason
        refreshed = path.read_text(encoding="utf-8")
        assert refreshed != before and "retouche à la main" in refreshed, "the same form: the values refreshed, the engineer's line kept"
        layers.chosen_spin.setValue(5.0)
        assert tab.save(), tab.ctx.reason
        after = path.read_text(encoding="utf-8")
        assert after != refreshed and "retouche à la main" in after, "a value written in place of the tenth above the sum: the same form, refreshed"
        assert unfold.status(here, "AU-95", kind="dead-load").matches and "dead-load" in unfold.AUTO_REGENERATE
        # D-15: the drawing of the build-up, a module of the right pane, opened in a window of its own by ⧉
        pane = tab.service("modules").pane
        shown = pane.open_window("drawing")
        assert "drawing" in pane.modules and shown.body is not pane.modules["drawing"].body, "⤢: a window whose body follows its size (UI-002)"
        shown.close()
        tab.dirty = False
