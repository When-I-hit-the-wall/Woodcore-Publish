"""The «Vent» tab on the type «Calcul» (calc/tools/wind_tab.py, calc/domains/wind_view.py; spec 2026-10-23-onglet-vent-briques, V5: UI-001 to UI-027, REQ-017, ARCH-013), in the example project, off screen.

What is held:

* **a class of parameters** on the type «Calcul», registered in place of the old frame -- `load_tab.py` gone, its list's words `ld_` in load_words.py;
* **the form in four sections**, in the prototype's order: q_p0, the terrain, b · d · h on one line, z «= h», c_d; the table of Annexe C, what it says, its figure of the norm and the model in 3D; c_red, the force coefficients, the forces per φ, formula (15), the forces in 3D; the pressure coefficients with the openings' column marked, ĉ_pe, the detail per φ, the openings on the line of their words -- shown only for a table that has them --, the formula of q_k, the loads in 3D;
* **the hovers by keys**: a cell of the detail lights its surface and frames the c_pe and c_pi that gave it; a result Q_k lights its column of forces; a reference area its face alone (UI-013, UI-021);
* **the results in 3D**: their directions the table's rows and «every direction», pinnable, their window following its size (UI-014, UI-018);
* **the right pane** (UI-019, D-34): «Résultats» with c_h, q_p, c_red, the global forces at their φ and the walls, the roof and the local areas, pressure max and suction max at their φ, each cell hovered lighting its surface; the module «Bâtiment»;
* **the switch «Norme / Modèle 3D»** (UI-005, D-35): one view at a time, the same in the section and the module; the facts with the table's title in the window's language;
* **the safety net**: a building without geometry shows its figure of the norm and no model (UI-026);
* **the words**: every message, every excerpt of the declaration, in three languages; the excerpts exist;
* **saved and exported**, its file written with the figure of the norm cut into Variable-loads/Wind/Exports/Figures/ (REQ-017).
"""

TIER = "fast"  # tests/run_tests.py --fast

import json
import os
import sys

import conftest
import project
from i18n import strings
from conftest import ROOT

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


def _tab():
    if "tab" not in _STATE:
        _qt()
        import project_template
        here = project_template.create(conftest.tmpdir("wind_tab") / "Halle", "Halle", document_language="fr", report_language="fr")
        with project.using(here):
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            window.mode = "rs"
            window.apply_mode()
            tab = next(t for t in window.tabs if getattr(t, "KEY", None) == "tab_ac_wind")
            tab.new()
            form = tab.service("form")
            _select(form.fields["table"].combo, "36")
            for key, value in (("b", 24.0), ("d", 12.0), ("h", 6.0)):
                form.fields[key].spin.setValue(value)
        _STATE.update(tab=tab, here=here, window=window)
    return _STATE["tab"]


def _select(combo, data):
    index = combo.findData(data)
    assert index >= 0, data
    combo.setCurrentIndex(index)


def test_the_wind_is_a_class_of_parameters_on_the_type_calcul_and_the_old_frame_is_gone():
    import calc_tab
    import tab_registry
    import wind_tab
    tab = _tab()
    assert isinstance(tab, wind_tab.WindTab) and isinstance(tab, calc_tab.CalcTab)
    assert dict(tab_registry.TABS)["tab_ac_wind"] is wind_tab.WindTab
    assert not (TOOLS / "load_tab.py").exists(), "LoadTab removed (ARCH-013)"
    own = {k for k, v in vars(wind_tab.WindTab).items() if not k.startswith("__") and k != "staticMetaObject"}
    assert own <= {"KEY", "MODULE", "ID_PREFIX", "LIST_KEY", "EMPTY_KEY"}, own


def test_the_form_is_four_sections_in_the_prototypes_order():
    tab = _tab()
    form = tab.service("form")
    assert list(form.sections) == ["basic", "building", "reduction", "pressure"]
    assert [form.sections[s].title.text() for s in form.sections] == [tab.t("wi_s_" + s) for s in ("basic", "building", "reduction", "pressure")]
    assert form.rows["b"][1] is form.rows["d"][1] is form.rows["h"][1], "b · d · h on one line"
    z = form.fields["z"]
    assert z.special is not None and z.special.isChecked() and tab.draft()["z"] is None, "z = h by default"
    assert set(form.blocks) == {"facts", "building_views", "cred", "cf", "forces", "forces_formula", "forces3d", "cp", "peak", "perphi", "openings_row", "pressure_formula", "loads3d"}
    facts = form.blocks["facts"].body.label.text()
    title = {"fr": "Coefficients pour h : b : d", "de": "Beiwerte für h : b : d", "en": "Beiwerte für h : b : d"}[tab.app.lang]   # the edition's, English reading German
    assert "36" in facts and "0,5 : 2 : 1" in facts and title in facts and ("toiture 30°" in facts) == (tab.app.lang == "fr"), facts
    cp = tab.ctx.blocks["cp"]
    assert [c["label"] for c in cp["columns"] if c["marked"]] == ["c_pi glm."], "the openings' column chosen, marked"
    assert [strings.translate("c_pi glm.", lang) for lang in ("de", "fr", "en")] == ["c_pi glm.", "c_pi rép.", "c_pi unif."], "said in the window's language (UI-027)"
    widget, holder = form.rows["openings"][1], form.rows["openings"][0]
    assert holder.isRowVisible(widget)
    _select(form.fields["table"].combo, "46")
    assert not holder.isRowVisible(widget), "an open building takes each surface's own c_pi: no openings to choose"
    _select(form.fields["table"].combo, "36")
    assert holder.isRowVisible(widget)


def test_the_hovers_light_and_frame_what_gave_each_number():
    """UI-013, UI-021: a cell of the detail per φ lights its surface on the model and frames the c_pe and c_pi cells that gave it; a result Q_k lights its column of forces and frames its extreme; b·h lights face A alone."""
    tab = _tab()
    form = tab.service("form")
    lit, framed = tab.ctx.hover_element("q:A:0")
    assert "surf:A" in lit and any(k.startswith("cell:cpe:A:0") for k in framed) and any(k.startswith("cell:cpi:rep:0") for k in framed)
    cp = form.blocks["cp"].body
    assert any(e.startswith("cell:cpe:A:0") for e in cp.framed_ids())
    lit, framed = tab.ctx.hover_element("var:Qk_max_cf1")
    assert {"Q:cf1:0", "Q:cf1:1", "Q:cf1:2", "Q:cf1:3"} <= lit and len(framed) == 1
    assert tab.ctx.hover_element("aref:bh") == ({"aref:bh", "surf:A"}, set())
    tab.ctx.hover_element(None)


def test_the_results_in_3d_offer_the_tables_directions_and_are_pinned_with_a_window_that_follows():
    tab = _tab()
    form = tab.service("form")
    for key in ("forces3d", "loads3d"):
        body = form.blocks[key].body
        assert list(body.direction_buttons) == ["0°", "15°", "45°", "90°", "max"], key
        assert body.direction_buttons["max"].text() == tab.t("wi_max") and form.blocks[key].pin is not None
    form.blocks["forces3d"].pin.click()
    pane = tab.service("modules").pane
    assert "b:forces3d" in pane.modules and pane.modules["b:forces3d"].spec.fills_window
    window = pane.open_window("b:forces3d")
    window.resize(900, 700)
    window.layout().activate()
    assert window.body.width() > 800
    window.close()
    pane.remove("b:forces3d")
    data = tab.ctx.blocks["forces3d"]
    scene = data["build"]({"sign": "+"})
    labels = [p.label for p in scene.primitives if getattr(p, "key", "").startswith("force:")]
    assert any("103,5" in l or "103.5" in l for l in labels), labels


def test_the_figure_and_the_model_are_one_view_at_a_time_the_same_in_the_section_and_the_module():
    """UI-005, D-35: «Norme» and «Modèle 3D» over the building, one shown at a time, the choice the tab's -- the module «Bâtiment» follows the section."""
    tab = _tab()
    views = tab.service("form").blocks["building_views"].body
    assert list(views.view_buttons) == ["figure", "model"] and [b.text() for b in views.view_buttons.values()] == [tab.t("wi_v_figure"), tab.t("wi_v_model")]
    assert views.current() == "figure" and not views.children["model"].isVisibleTo(views) and views.children["figure"].isVisibleTo(views)
    views.view_buttons["model"].click()
    assert views.children["model"].isVisibleTo(views) and not views.children["figure"].isVisibleTo(views)
    module = tab.service("modules").pane.modules["building"].body
    other = next(w.body for w in module.blocks if w.body.block.key == "building_views")
    assert other.current() == "model" and other.view_buttons["model"].isChecked()
    views.view_buttons["figure"].click()


def test_the_right_pane_has_the_results_at_their_phi_and_the_building():
    """UI-019, D-34: the pane is the state, «Résultats» -- c_h, q_p, c_red, then the global forces and the walls, the roof and the local areas at their φ --, «Bâtiment» and Figure 9; a cell of a wall lights its surface and frames its c_pe and c_pi."""
    tab = _tab()
    pane = tab.service("modules").pane
    assert list(pane.modules)[:4] == ["state", "results", "building", "chart"], list(pane.modules)
    assert pane.modules["building"].spec.title == tab.t("wi_m_building") and pane.modules["building"].spec.fills_window
    results = pane.modules["results"].body
    assert set(results.rows) == {"ch", "qp", "cred_bh", "cred_dh"} and not results.tables.isVisibleTo(results)
    shown = {w.body.block.key: w.body for w in results.blocks if w.body.isVisibleTo(results)}
    assert {"res_forces", "res_walls", "res_roofs", "res_locs"} <= set(shown) and "res_points" not in shown
    forces = tab.ctx.blocks["res_forces"]
    assert forces["rows"][0]["label"] == "Q_k,1" and forces["rows"][0]["cells"][0]["text"] == "103.5 kN (0°)"
    walls = tab.ctx.blocks["res_walls"]
    assert [r["label"] for r in walls["rows"]] == ["A", "B", "C", "D"] and walls["rows"][0]["cells"][0]["text"] == "0.68 (0°)" and walls["rows"][1]["cells"][0]["text"] == "—"
    lit, framed = tab.ctx.hover_element("qx:A:max")
    assert "surf:A" in lit and "q:A:0" in lit and "cell:cpe:A:0" in framed
    lit, framed = tab.ctx.hover_element("var:Qk_max_cf1")
    assert "Q:cf1:0" in lit and framed == {"Q:cf1:0"}
    tab.ctx.hover_element(None)
    assert tab.ctx.tl("Druck max [kN/m²]") in ("pression max [kN/m²]", "max pressure [kN/m²]", "Druck max [kN/m²]")


def test_a_building_without_geometry_shows_its_figure_and_no_model():
    """UI-026: the geometry of Tableau 36 taken away -- the figure of the norm is there, the model is not, and nothing fails."""
    from domains import wind_geometry, wind_source
    tab = _tab()
    held = wind_geometry.data()["buildings"].pop("36")
    try:
        data = wind_source.blocks(tab.draft(), tab.ctx.instance)
        assert "figure" in data and "model" not in data and "forces3d" not in data
    finally:
        wind_geometry.data()["buildings"]["36"] = held


def test_every_message_and_excerpt_has_its_words_in_three_languages():
    import woodcore_gui_words
    import wind_tab_words
    from domains import wind_source
    from norms import excerpts
    codes = {"q_p0", "terrain", "dimension", "too_high", "z", "table", "c_d", "z_min", "iv_as_iii", "c_d_default", "c_red_outside", "ratio", "direct", "no_area", "openings_default", "no_library"}
    decl = wind_source.declaration()
    used = {e for f in decl.fields for e in f.excerpts} | {"tab" + n for n in wind_tab_words.NUMBERS} | {"fig" + n for n in wind_tab_words.NUMBERS}
    for lang in ("fr", "de", "en"):
        words = woodcore_gui_words.STRINGS[lang]
        assert all("wi_msg_" + c in words for c in codes), lang
        assert all("wi_x_" + e in words for e in used), [e for e in used if "wi_x_" + e not in words]
        for e in used:
            excerpts.excerpt(decl.norm, e, lang)


def test_the_case_saved_writes_its_file_with_the_norms_figure():
    """REQ-017, REQ-018: saved, the case's file is written at once, its figure of the norm cut into Variable-loads/Wind/Exports/Figures/ -- one file an edition -- and printed from level 3 on."""
    tab = _tab()
    here = _STATE["here"]
    with project.using(here):
        tab.service("identity").rows.id.setText("WL-01")
        assert tab.save(), tab.ctx.messages
        text = (here.root / "Variable-loads" / "Wind" / "WL-01.typ").read_text(encoding="utf-8")
        assert '#from-level(3)[#figure(image("/Variable-loads/Wind/Exports/Figures/WL-01-fig-fr.pdf"' in text
        figures = here.root / "Variable-loads" / "Wind" / "Exports" / "Figures"
        assert (figures / "WL-01-fig-fr.pdf").read_bytes().startswith(b"%PDF") and (figures / "WL-01-fig-de.pdf").is_file()
        exported = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        assert exported["domains"]["wind-load"]["instances"]["WL-01"]["figures"][0]["from_level"] == 3
        # «Affichage» names the file by its command, as the snow's (UI-023)
        assert tab.display.path().name == "WL-01.typ" and tab.display.command() == '#include domain-file("wind-load", "WL-01")'
