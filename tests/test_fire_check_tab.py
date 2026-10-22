"""The «Résistance au feu» tab (calc/tools/fire_check_tab.py, issue #46; docs/ui/tab-fire-resistance.md).

What is held: the tab last of «Sécurité structurale», in the report alone, with its icon and its words in three languages, every id of VKF 15-15's lists with its word; it lists the checks carrying `fire` and the other tabs never do (and the other way round); a check of each of its five kinds made, saved and read back, its kind then closed; a field linked to a variable saved with it; the duration following the building and written over in orange with «Reprendre»; the building saved to Woodcore-Datei/building.json and the checks exported again with it; Python's result the domain's; a project opened read-only refusing both writers.

⚠️ Built off-screen on a copy of the example project (conftest.project_copy), message boxes stubbed and nothing compiled -- the helpers are test_member_check_tab's.
"""

TIER = "fast"  # tests/run_tests.py --fast

import json

import conftest

import project

import test_member_check_tab as base


def _window():
    """A window of its own, on a copy of its own: the tests below write checks and a building."""
    if "fire" not in base._STATE:
        base._qt()
        here = conftest.project_copy("fire_check_tab")
        with project.using(here):
            import woodcore_gui
            window = woodcore_gui.MainWindow()
            window.mode = "rs"
            window.apply_mode()
        base._STATE["fire"] = (window, here)
    return base._STATE["fire"]


def _ftab(window):
    import fire_check_tab
    return next(t for t in window.tabs if isinstance(t, fire_check_tab.FireCheckTab))


def _set_building(tab, **values):
    for key, value in values.items():
        base._select(tab.building_boxes[key], value)


def test_the_tab_is_last_of_safety_in_the_report_alone():
    base._qt()
    import woodcore_gui
    import chrome
    groups = dict(woodcore_gui.NAV_GROUPS)
    assert groups["nav_safety"][-1] == "tab_mc_fire"
    assert "tab_mc_fire" in woodcore_gui.mode_tabs("rs") and "tab_mc_fire" not in woodcore_gui.mode_tabs("cu") and "tab_mc_fire" not in woodcore_gui.mode_tabs("bp")
    assert "tab_mc_fire" in chrome.ICONS
    words = {lang: woodcore_gui.STRINGS[lang]["tab_mc_fire"] for lang in ("fr", "de", "en")}
    assert words == {"fr": "Résistance au feu", "de": "Feuerwiderstand", "en": "Fire resistance"}
    assert words["fr"] != woodcore_gui.STRINGS["fr"]["tab_fire"]
    assert "save_building" in woodcore_gui.WRITERS


def test_every_id_of_vkf_15_15_has_its_word():
    base._qt()
    import fire_check_tab
    import woodcore_gui
    from norms import vkf
    for key in vkf.BUILDING_KEYS:
        assert set(fire_check_tab.AEAI_WORDS[key]) == set(vkf.building_ids(key)), key
        for words in fire_check_tab.AEAI_WORDS[key].values():
            assert all(woodcore_gui.STRINGS[lang].get(words) for lang in ("fr", "de", "en")), words


def test_a_check_of_each_kind_is_made_saved_and_read_back():
    window, here = _window()
    with project.using(here):
        tab = _ftab(window)
        _set_building(tab, height="medium", use="housing", concept="construction", storeys="several")
        made = []
        for kind in ("bending", "shear", "buckling", "compression", "tension"):
            base._fresh(tab)
            base._select(tab.kind_box, kind)
            base._select(tab.section_box, "rec")
            tab.b_spin.setValue(160)
            tab.h_spin.setValue(240)
            base._select(tab.grade_box, "GL24h")
            base._select(tab.moisture_box, 1)
            if kind == "shear":
                tab.extra_spins["V_z"].setValue(12)
            else:
                tab.n_spin.setValue(20)
            if kind == "bending":
                tab.extra_spins["M_y"].setValue(8)
            with base._boxes():
                assert tab.save() is not False
            cid = tab.current_id
            made.append(cid)
            source = json.loads((here.checks_dir / ("%s.json" % cid)).read_text(encoding="utf-8"))
            assert source["kind"] == kind and source["schema_version"] == "1.2" and source["fire"]["duration"] is None, source
            assert cid.startswith("FE-")
            # saved: the kind is closed
            assert not tab.kind_box.isEnabled()
        exported = json.loads((here.data_dir / "checks.json").read_text(encoding="utf-8"))
        # 1.6 where a check is printed unfolded -- the example's are (spec 2026-10-15, ARCH-007; spec 2026-10-21-commandes-typst-refonte, ARCH-011) --, else 1.5 where a duration VKF 15-15 requires is cited by it (spec 2026-10-20-indices-et-niveaux, REQ-001), 1.2 otherwise
        checks = exported["checks"].values()
        from domains import member_check
        assert exported["schema_version"] == ("1.6" if any(member_check.is_unfolded(r) for r in checks) else "1.5" if any((r.get("fire") or {}).get("required") for r in checks) else "1.2")
        for cid in made:
            record = exported["checks"][cid]
            assert record["calculable"], (cid, record["reason"])
            assert (record["fire"]["duration"], record["fire"]["duration_from"]) == (60, "vkf")
        # this tab lists them, and no other tab does
        tab.reload_list()
        assert set(made) <= set(tab.ids)
        import member_check_tab
        for other in window.tabs:
            if isinstance(other, member_check_tab.MemberCheckTab) and other is not tab:
                other.reload_list()
                assert not set(made) & set(other.ids), (other.KEY, other.ids)
                assert not set(tab.ids) & set(other.ids)
        # read back: the form holds what was saved
        tab.load(made[0])
        assert tab.kind_box.currentData() == "bending" and tab.extra_spins["M_y"].value() == 8


def test_the_duration_follows_the_building_and_is_written_over():
    window, here = _window()
    with project.using(here):
        tab = _ftab(window)
        base._fresh(tab)
        _set_building(tab, height="low", use="office", concept="construction", storeys="several")
        assert tab.duration_spin.value() == 30 and tab.duration_spin.suffix() == tab.t("mc_fire_follows", table="1")
        assert not tab.duration_back.isVisible()
        tab.duration_spin.setValue(60)
        assert tab.duration_stated and tab.draft()["fire"]["duration"] == 60
        assert "R 30" in tab.duration_note.text()
        tab.take_back_duration()
        assert not tab.duration_stated and tab.draft()["fire"]["duration"] is None and tab.duration_spin.value() == 30
        # the top storey: note [1], no requirement, said
        tab.top_box.setChecked(True)
        assert "[1]" in tab.duration_note.text()
        assert tab.record is not None and not tab.record["calculable"]
        tab.top_box.setChecked(False)
        base._fresh(tab)


def test_the_building_is_saved_and_the_checks_follow_it():
    window, here = _window()
    with project.using(here):
        tab = _ftab(window)
        base._fresh(tab)
        _set_building(tab, height="high", use="office", concept="construction", storeys="several")
        with base._boxes():
            assert tab.save_building() is True
        saved = json.loads(here.building_file.read_text(encoding="utf-8"))
        assert saved == {"schema_version": "1.0", "height": "high", "use": "office", "concept": "construction", "storeys": "several"}
        exported = json.loads((here.data_dir / "checks.json").read_text(encoding="utf-8"))
        followed = [r for r in exported["checks"].values() if r.get("fire") and r["fire"]["duration_from"] == "vkf"]
        assert followed and all(r["fire"]["duration"] == 90 for r in followed)
        # an incomplete building is refused, saying what is missing
        base._select(tab.building_boxes["use"], None)
        with base._boxes() as shown:
            assert tab.save_building() is False
        assert shown and "complet" in shown[0]
        tab.fill_building()


def test_python_s_result_is_the_domain_s():
    window, here = _window()
    with project.using(here):
        tab = _ftab(window)
        base._fresh(tab)
        base._select(tab.kind_box, "bending")
        base._select(tab.section_box, "rec")
        tab.b_spin.setValue(140)
        tab.h_spin.setValue(200)
        base._select(tab.grade_box, "C24")
        base._select(tab.moisture_box, 1)
        tab.extra_spins["M_y"].setValue(1.9375 * 25 / 8)
        tab.duration_spin.setValue(60)
        for side, on in (("bottom", True), ("top", False), ("left", True), ("right", True)):
            tab.side_boxes[side].setChecked(on)
        tab.refresh(preview=False)
        from domains import member_check
        result = member_check.compute(tab.record)
        # the field holds two decimals: 6.05 kNm on the workbook's residual section, W_y,fi 105 125 mm³, against 1.8 · 14.1
        assert abs(result["eta"] - 6.05e6 / 105125 / (1.8 * 14.1)) < 1e-9
        assert "2.268" in tab.verdict_label.text() and "✘" in tab.verdict_label.text()
        base._fresh(tab)


def test_a_linked_force_is_saved_with_its_link():
    window, here = _window()
    with project.using(here):
        tab = _ftab(window)
        base._fresh(tab)
        base._select(tab.kind_box, "shear")
        tab.extra_spins["V_z"].setValue(10)
        wrapper = tab.linkables["V_z"]
        wrapper.set_link({"domain": "formula", "instance": "F1", "var": "V", "origin": "formulas"}, {})
        draft = tab.draft()
        assert draft["links"]["V_z"]["var"] == "V" and draft["schema_version"] == "1.2"
        wrapper.set_link(None, {})
        base._fresh(tab)


def test_a_read_only_project_refuses_both_writers():
    window, here = _window()
    with project.using(here):
        tab = _ftab(window)
        base._fresh(tab)
        window.read_only = True
        try:
            with base._boxes():
                assert tab.save() is False
                assert tab.save_building() is False
        finally:
            window.read_only = False
        base._fresh(tab)
