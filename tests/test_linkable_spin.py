"""A field of the window that follows a variable of the export (calc/tools/linkable_spin.py, spec docs/requirements/completed/2026-10-11-variables-liees-champs-et-textes.md, UI-001, UI-002, UI-003, REQ-008).

What is held, on the «Traction» tab of a copy of the example project:

* **the button** brings the «Variables» tab forward in its choosing mode, the navigation and Ctrl+n off, and lists only what the field may take: a domain with no variable of the field's dimension is not offered, nor a document's registry (UI-001, UI-003);
* **a variable refused** cannot be taken; **«Annuler»** gives the tab back unchanged;
* **a variable taken** comes back into the tab that asked, the field read-only showing its value, the variable named under it, the draft carrying the link at schema_version 1.1 (UI-002, D-17);
* **the factor** changes the value; **«Délier»** leaves a typed field keeping its value (REQ-008);
* **a variable gone** shows the last value in the theme's warning colour, «Introuvable» (D-06);
* **a section that follows its position** takes no variable: its button is closed;
* every field of the perimeter has its button, and no list has one (REQ-009, the member checks).

⚠️ Built off-screen; nothing here compiles Typst.
"""

TIER = "fast"  # tests/run_tests.py --fast

import sys

import conftest
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
        here = conftest.project_copy("linkable_spin")
        with project.using(here):
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            window.mode = "rs"
            window.apply_mode()
        _STATE.update(window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tabs(window):
    import member_check_tab
    import variables_tab
    tension = next(t for t in window.tabs if isinstance(t, member_check_tab.TensionTab))
    listing = next(t for t in window.tabs if isinstance(t, variables_tab.VariablesTab))
    return tension, listing


def _listed_domains(listing):
    from PySide6.QtCore import Qt
    return [tuple(listing.domain_list.topLevelItem(i).data(0, Qt.ItemDataRole.UserRole)) for i in range(listing.domain_list.topLevelItemCount())]


def test_a_field_is_linked_through_the_variables_tab_and_unlinked():
    window, here = _window()
    import theme
    import variables_tab
    from domains import links, member_check
    with project.using(here):
        tab, listing = _tabs(window)
        window.tab_widget.setCurrentWidget(tab)
        tab.load("ZT-01")
        tab.dirty = False
        wrapper = tab.linkables["N"]
        assert wrapper.link() is None and not tab.n_spin.isReadOnly()

        # the button: «Variables» in front, the rest closed, only what a force in kN may take
        wrapper.button.click()
        assert window.tab_widget.currentWidget() is listing and not window.nav.isEnabled() and not listing.pick_bar.isHidden()
        assert all(not s.isEnabled() for s in window.shortcuts)
        assert "N" in listing.pick_label.text() and "kN" in listing.pick_label.text()
        listed = _listed_domains(listing)
        assert listed and all(origin in (variables_tab.EXPORT, variables_tab.FORMULAS) for origin, _name in listed), listed
        assert (variables_tab.FORMULAS, "poutre-p1") not in listed, "a domain with no force in it is not offered"
        for key in listed:
            assert any(links.compatible(var.unit, "kN") and var.is_number for var in listing.domains[key].variables), key
        live = next(k for k, d in listing.domains.items() if k[0] == variables_tab.EXPORT and d.address == ("live-load", "A1"))
        # a variable of another dimension is not taken
        listing.select_key((*live, "q_k"))
        listing.pick_chosen()
        assert window.tab_widget.currentWidget() is listing and not listing.pick_bar.isHidden()
        listing.end_pick(None)                                   # «Annuler»
        assert window.nav.isEnabled() and window.tab_widget.currentWidget() is tab and wrapper.link() is None and not tab.dirty

        # a variable taken: the value, the name under the field, the link in the draft
        wrapper.button.click()
        listing.select_key((*live, "Q_k"))
        listing.pick_chosen()
        assert window.nav.isEnabled() and window.tab_widget.currentWidget() is tab
        assert tab.n_spin.value() == 2.0 and tab.n_spin.isReadOnly() and tab.dirty
        assert wrapper.link() == {"domain": "live-load", "instance": "A1", "var": "Q_k"}
        assert "Q_k" in wrapper.chip.text() and not wrapper.linked_row.isHidden()
        draft = tab.draft()
        assert draft["links"] == {"N": {"domain": "live-load", "instance": "A1", "var": "Q_k"}}
        assert draft["schema_version"] == member_check.LINKED_SCHEMA_VERSION
        member_check.check_source(draft)

        # the factor, then «Délier»
        wrapper.factor.setValue(1.5)
        assert tab.n_spin.value() == 3.0 and tab.draft()["links"]["N"]["factor"] == 1.5
        wrapper.unlink_button.click()
        assert wrapper.link() is None and not tab.n_spin.isReadOnly() and tab.n_spin.value() == 3.0
        draft = tab.draft()
        assert "links" not in draft and draft["schema_version"] == member_check.SOURCE_SCHEMA_VERSION

        # a variable gone: the last value, in the warning colour
        wrapper.set_link(links.make("live-load", "A1", "gone"))
        assert tab.n_spin.value() == 3.0 and "gone" in wrapper.chip.text()
        assert theme.colour("warning") in wrapper.chip.styleSheet()
        wrapper.set_link(None)
        tab.dirty = False


def test_every_field_of_the_perimeter_has_its_button_and_no_list_has_one():
    window, here = _window()
    import member_check_tab
    import linkable_spin
    from domains import member_check
    from PySide6.QtWidgets import QComboBox
    with project.using(here):
        for tab in window.tabs:
            if not isinstance(tab, member_check_tab.MemberCheckTab):
                continue
            # each tab is held to its own domain's list: the «Acier» tabs (steel_tab.py) are member check tabs writing steel_check's sources (issue #51)
            allowed = set(tab.DOMAIN.LINKABLE)
            assert set(tab.linkables) <= allowed, (type(tab).__name__, set(tab.linkables) - allowed)
            if tab.DOMAIN is member_check:
                assert {"N", "alpha", "section.b", "section.h", "section.d"} <= set(tab.linkables), type(tab).__name__
            for wrapper in tab.findChildren(linkable_spin.LinkableSpin):
                assert not isinstance(wrapper.spin, QComboBox)
            assert not any(isinstance(w.parent(), linkable_spin.LinkableSpin) for w in tab.findChildren(QComboBox))
        kinds = {type(t).__name__: set(t.linkables) for t in window.tabs if isinstance(t, member_check_tab.MemberCheckTab)}
        assert {"l", "w"} <= kinds["CompressionTab"]
        assert {"M_y", "M_z"} <= kinds["BendingTab"]
        assert {"l_y", "l_z", "beta_y", "beta_z"} <= kinds["BucklingTab"]
        assert {"M_y", "M_z", "a", "sigma_m_crit", "l_y", "beta_z"} <= kinds["LateralTab"]
        assert {"V_z", "V_y"} <= kinds["ShearTab"]
        assert {"N", "A_net"} <= kinds["SteelTensionTab"]
        assert {"N", "M_y", "M_z"} <= kinds["SteelBendingTab"]
        assert {"V_z", "V_y", "M_y"} <= kinds["SteelShearTab"]


def test_a_section_that_follows_its_position_takes_no_variable():
    window, here = _window()
    with project.using(here):
        tab, _listing = _tabs(window)
        tab.load("ZT-01")                     # T001's section, followed
        assert tab.section_box.currentData() is None
        assert not tab.linkables["section.b"].button.isEnabled()
        tab.dirty = False


def test_a_static_model_s_point_and_load_follow_variables_and_are_saved_at_1_2():
    """D-05, UI-005: a point's x is linked through the same button; a load's magnitude names its variable through the «Variables» tab, no list of domains of its own; saved, the model is 1.2, the point holds the value now and the magnitude its last value."""
    import json
    import linkable_spin
    import statics_tab
    import variables_tab
    from domains import statics
    window, here = _window()
    with project.using(here):
        tab = next(t for t in window.tabs if isinstance(t, statics_tab.StaticsTab))
        _tension, listing = _tabs(window)
        window.tab_widget.setCurrentWidget(tab)
        source = statics.new_source("LK1")
        source.update(points=[{"id": "P1", "x": 0, "z": 0}, {"id": "P2", "x": 3, "z": 0}],
                      members=[{"id": "B1", "kind": "bar", "p1": "P1", "p2": "P2"}],
                      supports=[{"id": "A1", "point": "P1", "type": "pinned"}, {"id": "A2", "point": "P2", "type": "roller"}],
                      point_loads=[{"id": "F1", "point": "P2", "direction": "vertical", "label": "F", "show": "name+value",
                                    "magnitude": {"value": 2.0, "unit": "kN"}}])
        tab.open_source(source, None, False)
        tab.canvas.select(("points", "P2"))
        wrappers = {w.field: w for w in tab.selection_group.findChildren(linkable_spin.LinkableSpin)}
        assert set(wrappers) == {"x", "z"}, wrappers
        snow = next(k for k, d in listing.domains.items() if k[0] == variables_tab.EXPORT and d.address == ("snow-load", "SL"))
        wrappers["x"].button.click()
        assert window.tab_widget.currentWidget() is listing and "m" in listing.pick_label.text()
        listing.select_key((*snow, "L"))
        listing.pick_chosen()
        assert window.tab_widget.currentWidget() is tab
        p2 = next(p for p in tab.source["points"] if p["id"] == "P2")
        assert p2["x"] == 17.5 and p2["links"] == {"x": {"domain": "snow-load", "instance": "SL", "var": "L"}}, p2

        # the load: its variable chosen in «Variables», only forces, loads per metre or square metre and moments offered
        tab.canvas.select(("point_loads", "F1"))
        load = tab.source["point_loads"][0]
        tab.set_magnitude_kind(load, False)
        assert window.tab_widget.currentWidget() is listing
        live = next(k for k, d in listing.domains.items() if k[0] == variables_tab.EXPORT and d.address == ("live-load", "A1"))
        listing.select_key((*snow, "L"))      # metres: no load
        listing.pick_chosen()
        assert window.tab_widget.currentWidget() is listing
        listing.select_key((*live, "Q_k"))
        listing.pick_chosen()
        assert window.tab_widget.currentWidget() is tab
        assert tab.source["point_loads"][0]["magnitude"] == {"domain": "live-load", "instance": "A1", "var": "Q_k"}

        assert tab.save()
        saved = json.loads((here.statics_dir / "LK1.json").read_text(encoding="utf-8"))
        assert saved["schema_version"] == statics.LINKED_SCHEMA_VERSION
        assert saved["point_loads"][0]["magnitude"]["last"] == {"value": 2, "unit": "kN"}
        statics.check_source(saved, "LK1.json")
        exported = json.loads((here.data_dir / "statics.json").read_text(encoding="utf-8"))
        assert exported["schema_version"] == (statics.ROOTED_EXPORT_VERSION if here.has_folders else statics.LINKED_EXPORT_VERSION) and exported["models"]["LK1"]["links"][0]["field"] == "x"   # laid out by folders, 1.3 contains 1.2 (issue #64)
        tab.dirty = False


def test_a_project_opened_read_only_closes_the_button():
    """ARCH-RISK-009: a link is a change to the project's sources, which a project opened read-only refuses; the button is closed and does nothing."""
    _window()
    import linkable_spin
    from PySide6.QtWidgets import QDoubleSpinBox

    class App:
        read_only = True
        asked = []

        def begin_variable_pick(self, *args):
            self.asked.append(args)
            return True

    app = App()
    wrapper = linkable_spin.LinkableSpin(QDoubleSpinBox(), "kN", "N", lambda: app)
    assert not wrapper.button.isEnabled() and not wrapper.unlink_button.isEnabled()
    wrapper.set_editable(True)
    assert not wrapper.button.isEnabled()
    wrapper.pick()
    assert app.asked == []
    App.read_only = False
    wrapper.set_editable(True)
    assert wrapper.button.isEnabled()


def test_every_number_of_a_static_model_that_may_follow_a_variable_has_its_button():
    """REQ-009 for the static models (D-05): a point's x and z, a spring's stiffness, a rotational release's, the model's b_e and a load's own -- each a button; the label of a load, its colour and its show none."""
    import linkable_spin
    window, here = _window()   # calc/tools is on the path once the window is built: a tab's module is imported after it
    import statics_tab
    from domains import statics
    with project.using(here):
        tab = next(t for t in window.tabs if isinstance(t, statics_tab.StaticsTab))
        source = statics.new_source("LK2")
        width = {"value": 1.0, "unit": "m", "label": "b_e", "description": "", "show": True}
        source.update(points=[{"id": "P1", "x": 0, "z": 0}, {"id": "P2", "x": 3, "z": 0}, {"id": "P3", "x": 3, "z": 2}],
                      members=[{"id": "B1", "kind": "bar", "p1": "P1", "p2": "P2"},
                               {"id": "B2", "kind": "spring", "p1": "P2", "p2": "P3", "stiffness": {"value": 1000.0, "unit": "kN/m"}}],
                      supports=[{"id": "A1", "point": "P1", "type": "pinned"}, {"id": "A2", "point": "P3", "type": "fixed"}],
                      releases=[{"id": "G1", "member": "B1", "end": "end", "dof": "moment", "stiffness": {"value": 500.0, "unit": "kNm/rad"}}],
                      line_loads=[{"id": "q1", "member": "B1", "shape": "uniform", "direction": "vertical", "label": "q", "show": "name+value",
                                   "magnitude": {"value": 2.0, "unit": "kN/m²"}, "width": dict(width)}],
                      width=dict(width))
        tab.open_source(source, None, False)

        def fields(selection):
            tab.canvas.select(selection)
            return sorted((w.field, w.unit) for w in tab.selection_group.findChildren(linkable_spin.LinkableSpin))

        assert fields(("points", "P2")) == [("x", "m"), ("z", "m")]
        assert fields(("members", "B2")) == [("k", "kN/m")]
        assert ("k", "kNm/rad") in fields(("members", "B1"))
        assert fields(("line_loads", "q1")) == [("b_e", "m")]
        tab.canvas.select(None)
        assert [w.field for w in tab.findChildren(linkable_spin.LinkableSpin) if w.isVisibleTo(tab)].count("b_e") >= 1
        tab.dirty = False


def test_a_model_saved_before_whose_load_names_a_variable_opens_linked_and_exports_as_it_did():
    """UI-005: a 1.1 model whose load names a variable of the export (the three lists' reference) is read, shown with that variable named and «Choisir…», and exported as before -- the magnitude's own `last` is the window's, written only when it saves."""
    import json
    from PySide6.QtWidgets import QLabel, QPushButton
    window, here = _window()   # calc/tools is on the path once the window is built: a tab's module is imported after it
    import statics_tab
    from domains import statics
    with project.using(here):
        source = statics.new_source("LK3")
        source.update(points=[{"id": "P1", "x": 0, "z": 0}, {"id": "P2", "x": 3, "z": 0}],
                      members=[{"id": "B1", "kind": "bar", "p1": "P1", "p2": "P2"}],
                      supports=[{"id": "A1", "point": "P1", "type": "pinned"}, {"id": "A2", "point": "P2", "type": "roller"}],
                      point_loads=[{"id": "F1", "point": "P2", "direction": "vertical", "label": "F", "show": "name+value",
                                    "magnitude": {"domain": "live-load", "instance": "A1", "var": "Q_k", "factor": 1.5}}])
        assert source["schema_version"] == "1.1"
        path = here.statics_dir / "LK3.json"
        path.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        data_before, _files, _notes = statics.prepare(here.statics_dir, statics.known_values(here.data_dir))
        assert "links" not in data_before["models"]["LK3"] and data_before["schema_version"] == statics.EXPORT_SCHEMA_VERSION
        tab = next(t for t in window.tabs if isinstance(t, statics_tab.StaticsTab))
        tab.load("LK3")
        tab.canvas.select(("point_loads", "F1"))
        texts = [w.text() for w in tab.selection_group.findChildren(QLabel)]
        assert any("Q_k" in text and "live-load" in text for text in texts), texts
        assert any(b.text() == tab.t("st_var_choose") for b in tab.selection_group.findChildren(QPushButton))
        assert not tab.dirty
        assert json.loads(path.read_text(encoding="utf-8")) == source, "opening writes nothing"
        path.unlink()
        tab.dirty = False


# --- lot 2: the connectors, the polar moments, the loads ----------------------------------------------

def _pick(window, listing, wrapper, address, var):
    """The button of `wrapper`, then `var` of the export's domain at `address` chosen in «Variables»."""
    import variables_tab
    wrapper.button.click()
    assert window.tab_widget.currentWidget() is listing, "the button brings «Variables» forward"
    key = next(k for k, d in listing.domains.items() if k[0] == variables_tab.EXPORT and d.address == address)
    listing.select_key((*key, var))
    listing.pick_chosen()


def test_a_connector_s_numbers_have_their_button_and_its_diameter_follows_a_load():
    """REQ-009 (lot 2): the connector's diameter and f_u,k and each member's α, a₁ have the button; the diameter linked to a load's length, scaled by a factor, comes back into the tab, the draft carrying the link at 2.1; no joint's variables are offered to a connector (ARCH-005)."""
    window, here = _window()
    import connectors_tab
    from domains import connector
    with project.using(here):
        tab = next(t for t in window.tabs if isinstance(t, connectors_tab.ConnectorsTab))
        _tension, listing = _tabs(window)
        window.tab_widget.setCurrentWidget(tab)
        tab.load("SD-10")
        keys = set(tab.link_fields)
        assert {("self", "diameter"), ("self", "dowel.f_u_k"), (0, "alpha"), (0, "a_1")} <= keys, keys
        wrapper = tab.link_fields[("self", "diameter")]
        wrapper.button.click()
        assert window.tab_widget.currentWidget() is listing
        listed = _listed_domains(listing)
        assert not any(listing.domains[k].address and listing.domains[k].address[0] in ("connection", "connector") for k in listed), listed
        listing.end_pick(None)
        # a load's length, in m, for a diameter in mm: 17.5 m is past the field's 60 mm until a factor scales it -- the form as it stands, the tab rebuilding it as it comes back
        _pick(window, listing, tab.link_fields[("self", "diameter")], ("snow-load", "SL"), "L")
        wrapper = tab.link_fields[("self", "diameter")]   # the form as it stands once the tab is shown again
        assert window.tab_widget.currentWidget() is tab and wrapper.link() == {"domain": "snow-load", "instance": "SL", "var": "L"}
        wrapper.factor.setValue(0.0005)
        assert abs(tab.diameter_box.value() - 8.8) < 1e-9, tab.diameter_box.value()   # 8.75 mm, shown at the field's one decimal
        draft = tab.draft()
        assert draft["links"]["diameter"]["factor"] == 0.0005 and draft["schema_version"] == connector.LINKED_SCHEMA_VERSION
        connector.check_source(draft, "SD-10.json")
        wrapper.unlink_button.click()
        assert "links" not in tab.draft() and tab.draft()["schema_version"] == connector.SOURCE_SCHEMA_VERSION
        tab.dirty = False


def test_a_polar_moment_s_trial_forces_are_saved_and_follow_a_script():
    """D-12: the trial forces are data of the calculation, in its draft; N linked to a script's force comes back as its value, at 4.1; a centre not placed by hand takes no variable, its buttons closed."""
    window, here = _window()
    import polar_tab
    from domains import connection
    with project.using(here):
        tab = next(t for t in window.tabs if isinstance(t, polar_tab.PolarTab))
        _tension, listing = _tabs(window)
        window.tab_widget.setCurrentWidget(tab)
        tab.load("VU-MP-1")
        assert set(tab.link_fields) == {"center.x", "center.z", "directions.N", "directions.V", "trial.N", "trial.V", "trial.M"}
        assert set(tab.draft()["trial"]) == {"N", "V", "M"}
        if not tab.manual_radio.isChecked():
            assert not tab.link_fields["center.x"].button.isEnabled()
        _pick(window, listing, tab.link_fields["trial.N"], ("script", "dreigelenk"), "V_d")
        assert window.tab_widget.currentWidget() is tab
        assert abs(tab.trial["N"].value() - 19.2) < 1e-9
        draft = tab.draft()
        assert draft["links"] == {"trial.N": {"domain": "script", "instance": "dreigelenk", "var": "V_d"}}
        assert draft["schema_version"] == connection.LINKED_SCHEMA_VERSION and abs(draft["trial"]["N"] - 19.2) < 1e-9
        connection.check_source(draft, "VU-MP-1.json")
        tab.link_fields["trial.N"].unlink_button.click()
        assert "links" not in tab.draft() and tab.draft()["schema_version"] == connection.SOURCE_SCHEMA_VERSION
        tab.dirty = False


def test_a_load_s_field_follows_another_load_and_a_circle_is_refused_as_it_is_chosen():
    """REQ-009 (lot 2), D-11, REQ-007: a snow load's h_0 follows a wind load's b; a script is not offered to a load; a link that would make two loads follow each other is refused as it is chosen, said in the status line; a dead load's layer has its buttons, its link travelling with the layer."""
    import json
    window, _here = _window()
    import load_tab
    from domains import links, snow_source, wind_source
    # a copy of its own: leaving a load tab saves its case and rebuilds calculations.json, which a project without its workbooks writes without their sheets -- the other tests read those
    here = conftest.project_copy("linkable_spin_loads")
    with project.using(here):
        # a wind load entered in Woodcore, exported: what the snow load follows -- a sheet of a workbook would be gone with the first save, the copy carrying no workbook
        import registry
        folder = here.sources_dir / wind_source.FOLDER
        folder.mkdir(parents=True, exist_ok=True)
        base = wind_source.new_source("WI-01")
        base["b"] = 12
        (folder / "WI-01.json").write_text(json.dumps(base, indent=2), encoding="utf-8")
        registry.export(here)
        snow = next(t for t in window.tabs if isinstance(t, load_tab.SnowTab))
        _tension, listing = _tabs(window)
        window.tab_widget.setCurrentWidget(snow)
        snow.new()
        assert {"h_0", "c_t", "length", "width", "alpha_1", "alpha_2"} == set(snow.linkables)
        snow.linkables["h_0"].button.click()
        listed = _listed_domains(listing)
        assert not any((listing.domains[k].address or ("",))[0] in ("script", "connection", "connector") for k in listed), listed
        listing.end_pick(None)
        _pick(window, listing, snow.linkables["h_0"], ("wind-load", "WI-01"), "b")
        assert window.tab_widget.currentWidget() is snow and snow.h0_spin.value() == 12
        draft = snow.draft()
        assert draft["links"]["h_0"]["domain"] == "wind-load" and draft["schema_version"] == snow_source.LINKED_SCHEMA_VERSION
        # a wind load on the disk that follows this snow load: linking back to it closes a circle
        sid = draft["id"]
        wind = wind_source.new_source("WI-77")
        wind["links"] = {"b": links.make("snow-load", sid, "h_0")}
        (folder / "WI-77.json").write_text(json.dumps(wind_source.stamp_version(wind), indent=2), encoding="utf-8")
        message = snow.refuse_link(links.make("wind-load", "WI-77", "b"))
        assert message and "WI-77" in message and sid in message, message
        assert snow.refuse_link(links.make("wind-load", "WI-01", "b")) is None
        (folder / "WI-77.json").unlink()
        snow.dirty = False
        dead = next(t for t in window.tabs if isinstance(t, load_tab.DeadLoadTab))
        dead.new()
        if dead.table.rowCount() == 0:
            dead.add_layer()
        cell = dead.table.cellWidget(0, 3)
        assert hasattr(cell, "link") and cell.unit == "mm"
        cell.set_link(links.make("wind-load", "WI-01", "h", factor=10))
        layer = dead.current_layers()[0]
        assert layer["links"]["thickness"]["instance"] == "WI-01" and dead.draft()["schema_version"] == "1.1"
        assert "chosen" in dead.linkables
        dead.dirty = False
    # «Variables» read again from the window's own copy, which the other tests of this file read
    with project.using(_here):
        listing.on_shown()   # the export's files read again, at once (the automatic reading of the documents is off for the suite)


def test_every_number_of_the_joints_and_loads_tabs_has_its_button_and_no_list_has_one():
    """REQ-009 (lot 2): in «Moyens d'assemblage» (a Holz-Holz and a Stahl-Holz joint), «Moments polaires», «Poids propre et surcharge» (a layer in its table), «Neige» and «Vent», every number field -- a QDoubleSpinBox -- sits in a LinkableSpin, and no list does: the moisture class, the grades, the kinds, the materials take no variable (T6)."""
    window, here = _window()
    import connectors_tab
    import linkable_spin
    import load_tab
    import polar_tab
    from PySide6.QtWidgets import QComboBox, QDoubleSpinBox

    def wrapper_of(widget):
        parent = widget.parentWidget()
        while parent is not None and not isinstance(parent, linkable_spin.LinkableSpin):
            parent = parent.parentWidget()
        return parent

    def check(tab, what):
        numbers = tab.findChildren(QDoubleSpinBox)
        assert numbers, what
        # a row the form hides is no field of this source: a Stahl-Holz joint's member t, whose thickness is the steel half's b
        loose = [(n.suffix(), n.minimum(), n.maximum()) for n in numbers if wrapper_of(n) is None and n.isVisibleTo(tab)]
        assert not loose, f"{what}: a number without its button: {loose}"
        lists = [c for c in tab.findChildren(QComboBox) if wrapper_of(c) is not None]
        assert not lists, f"{what}: a list with a variable button"

    with project.using(here):
        joints = next(t for t in window.tabs if isinstance(t, connectors_tab.ConnectorsTab))
        joints.load("SD-10")
        for assembly in ("Holz-Holz zweischnittig", "Stahl-Holz, Schlitzbleche"):
            joints.assembly_box.setCurrentIndex(joints.assembly_box.findData(assembly))
            check(joints, assembly)
        assert {(0, "t"), (0, "plates.slot"), (0, "plates.ratio"), ("self", "diameter"), ("self", "dowel.f_u_k"), (0, "alpha"), (0, "a_1")} <= set(joints.link_fields)
        joints.dirty = False
        check(next(t for t in window.tabs if isinstance(t, polar_tab.PolarTab)), "polar")
        dead = next(t for t in window.tabs if isinstance(t, load_tab.DeadLoadTab))
        dead.new()
        if dead.table.rowCount() == 0:
            dead.add_layer()
        check(dead, "dead load")
        dead.dirty = False
        snow = next(t for t in window.tabs if isinstance(t, load_tab.SnowTab))
        check(snow, "snow")
        wind = next(t for t in window.tabs if isinstance(t, load_tab.WindTab))
        check(wind, "wind")
        assert set(wind.linkables) == {"q_p0", "b", "d", "h", "z", "c_d"}
