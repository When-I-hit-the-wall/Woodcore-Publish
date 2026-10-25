"""The «Matériaux» tab (calc/tools/materials_tab.py on library_tab.LibraryTab; spec docs/requirements/active/2026-10-24-onglet-materiaux.md, UI-001 to UI-008, ARCH-005, ARCH-006, REQ-006, REQ-007, REQ-012; issue #110).

What is held, in a window on a copy of the example project, the library in the suite's own folder:

* **UI-001, ARCH-005** -- the last tab, alone in «Autres», in the three documents, bound to none, `project=False`: never greyed, never stale after an export; its module never names the project;
* **UI-002** -- a material saved in a project opened read only;
* **UI-003** -- the search narrowing the list and opening its categories, «Supprimer» off on a shipped material;
* **UI-004** -- a shipped material read only, its band and «Dupliquer dans ma bibliothèque»; OSB/3's ρ_k and weight apart, each with its role;
* **UI-005, UI-006** -- a member typed by f_m,k alone shows 14.1 in italics, its rule in its tooltip; OSB/3's grid 18.0 / 16.4 / 14.8 characteristic, 10.5 / 9.6 / 8.6 design;
* **UI-007** -- a click on a row's source label selects it and shows «La source», which flashes; ⤢ opens it large and Échap closes it; the state and «Disponible dans» are the domain's;
* **UI-008** -- C24's source is Tabelle 8's excerpt, cut from the shipped PDF;
* **REQ-007** -- «+ Nouveau» a panel, saved, read back from the disk; «Supprimer» takes it away; a draft unsaved kept through a rebuild of the window.
"""

TIER = "window"

import ast
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conftest
import project
import usersettings

TOOLS = conftest.ROOT / "calc" / "tools"
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
        os.environ[usersettings.MATERIALS_ENV] = str(conftest.tmpdir("materials-tab-library"))
        here = conftest.project_copy("materials_tab")
        with project.using(here):
            import woodcore_gui
            window = woodcore_gui.MainWindow()
        _STATE.update(window=window, here=here)
    return _STATE["window"], _STATE["here"]


def _tab(window):
    return next(t for t in window.tabs if getattr(t, "KEY", None) == "tab_materials")


def test_the_tab_is_the_last_alone_in_others_and_the_engineers_not_the_projects():
    _qt()
    import tab_registry
    spec = tab_registry.SPECS[-1]
    assert (spec.key, spec.group, spec.documents, spec.mode_bound, spec.project) == ("tab_materials", "nav_others", tab_registry.ALL, False, False)
    assert tab_registry.PROJECT_FREE == ("tab_materials",) and tab_registry.NAV_GROUPS[-1] == ("nav_others", ("tab_materials",))
    assert spec.factory not in tab_registry.GUARDED_TABS
    import tab_guard
    assert not set(tab_guard.WRITERS) & set(dir(spec.factory)), "no writer name the read-only guard would wrap"
    for module in ("materials_tab.py", "library_tab.py", "materials_list.py", "materials_sheet.py", "materials_pane.py"):
        tree = ast.parse((TOOLS / module).read_text(encoding="utf-8"))
        named = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "project"}
        assert "current" not in named, "%s reads the project" % module
    window, here = _window()
    with project.using(here):
        assert window.available("tab_materials")
        window.refresh_lightly()
        assert "tab_materials" not in window.stale_tabs


def test_the_search_narrows_the_list_and_a_shipped_material_is_read_only():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        lst, sheet = tab.service("list"), tab.service("sheet")
        lst.query.setText("")
        everything = lst.tree.topLevelItemCount()
        lst.query.setText("isolation")
        assert lst.tree.topLevelItemCount() < everything and all(lst.tree.topLevelItem(i).isExpanded() for i in range(lst.tree.topLevelItemCount()))
        lst.query.setText("")
        tab.ctx.select("sia265:C24")
        assert not lst.delete_button.isEnabled() and lst.duplicate_button.isEnabled()
        assert sheet.name_edit.isReadOnly() and sheet.dup_mine.isVisibleTo(tab)
        assert sheet.grid.item(0, 2).text() == "14.1" and not sheet.grid.item(0, 2).font().italic()      # Tabelle 8's own value: typed by the norm
        modules = tab.service("modules")
        source = modules.bodies["source"]
        from norm_bubble import ExcerptView
        views = source.findChildren(ExcerptView)
        assert views and views[0].items[0].page == 25 and views[0].items[0].norm == "sia265-2021-materials-excerpts"


def test_osb3_shows_its_grid_and_its_two_densities():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        tab.ctx.select("sia265-1:osb3")
        sheet = tab.service("sheet")
        sheet._mode("k")
        row = next(r for r, x in enumerate(sheet.panel_rows) if x == ("value", "plate", "f_m", "par"))
        assert [sheet.grid.item(row, 2 + c).text() for c in range(3)] == ["18", "16.4", "14.8"]
        rho = next(r for r, x in enumerate(sheet.panel_rows) if x[0] == "rho")
        assert [sheet.grid.item(rho, 2 + c).text() for c in range(3)] == ["550"] * 3 and tab.ctx.t("mat_rho_role") in sheet.grid.item(rho, 0).text()
        assert sheet.weight_value.text() == "6.8" and sheet.weight_kg.text() == "= 680 kg/m³"
        sheet._mode("d")
        assert [sheet.grid.item(row, 2 + c).text() for c in range(3)] == ["10.5", "9.6", "8.6"]


def test_a_new_member_is_typed_deduced_and_saved_then_deleted():
    window, here = _window()
    from PySide6.QtWidgets import QMessageBox
    with project.using(here):
        tab = _tab(window)
        lst = tab.service("list")
        assert lst.new_material("member") and tab.ctx.dirty
        sheet = tab.service("sheet")
        assert not sheet.name_edit.isReadOnly()
        sheet._set_name(window.lang, "Mon BSH")
        sheet.grid.item(0, 1).setText("24")
        cell = sheet.grid.item(0, 2)
        assert cell.text() == "14.1" and cell.font().italic() and "24 / 1.7" in cell.toolTip() and "SIA 265 (3)" in cell.toolTip()
        assert sheet.grid.item(5, 2).text() == "1.5" and "3.3.2.2" in sheet.grid.item(5, 2).toolTip()
        states = tab.service("modules").bodies["state"]
        assert any("3" in label.text() for label in states.findChildren(__import__("PySide6.QtWidgets", fromlist=["QLabel"]).QLabel))
        mid = tab.ctx.current_id
        assert tab.ctx.save_entry() and not tab.ctx.dirty
        from domains import materials_user
        assert materials_user.find(mid)["values"] == {"f_m_k": 24.0}
        assert tab.service("list").delete_button.isEnabled()
        was = QMessageBox.question
        QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
        try:
            assert tab.ctx.delete_entry()
        finally:
            QMessageBox.question = was
        assert materials_user.find(mid) is None


def test_a_source_label_shows_the_source_large_and_a_pdf_is_copied():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        lst = tab.service("list")
        lst.query.setText("osb/4")
        head = lst.tree.topLevelItem(0)
        row = next(head.child(j) for j in range(head.childCount()) if head.child(j).data(0, 0x0100) == "sia265-1:osb4")
        lst._clicked(row, 1)
        assert tab.ctx.current_id == "sia265-1:osb4"
        modules = tab.service("modules")
        assert modules.pane.modules["source"].blinker.active() and not modules.pane.modules["source"].folded
        big = modules.open_big()
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtCore import QEvent
        assert not big.isHidden()      # the window itself is not shown under the suite
        from PySide6.QtGui import QShortcut
        escape = next(sc for sc in big.findChildren(QShortcut) if sc.key().toString() == "Esc")
        escape.activated.emit()
        assert big.isHidden()
        lst.query.setText("")
        assert lst.new_material("other")
        pdf = conftest.tmpdir("materials-tab-pdf") / "Fiche Isolant.pdf"
        pdf.write_bytes(b"%PDF-1.4 x")
        modules._dropped(str(pdf))
        assert tab.ctx.draft["source"] == {"kind": "pdf", "file": "sources/fiche-isolant.pdf"}
        tab.ctx.cancel()
        assert tab.ctx.current_id is None


def test_a_new_panel_with_its_pdf_is_saved_read_back_and_deleted_with_its_pdf():
    """REQ-007, REQ-012: «+ Nouveau» a panel, its PDF imported, saved and read back from the disk; «Annuler» puts back what was saved; «Supprimer» takes it and its PDF away."""
    window, here = _window()
    from PySide6.QtWidgets import QMessageBox
    from domains import materials_user
    with project.using(here):
        tab = _tab(window)
        assert tab.service("list").new_material("panel")
        sheet = tab.service("sheet")
        sheet._set_name(window.lang, "Trois plis mélèze")
        pdf = conftest.tmpdir("materials-tab-panel-pdf") / "Datenblatt Dreischicht.pdf"
        pdf.write_bytes(b"%PDF-1.4 panel")
        rel = sheet.import_pdf(str(pdf))
        mid = tab.ctx.current_id
        assert tab.ctx.save_entry()
        saved = materials_user.find(mid)
        assert saved["type"] == "panel" and saved["source"] == {"kind": "pdf", "file": rel}
        path = materials_user.source_path(saved)
        assert path.read_bytes() == b"%PDF-1.4 panel"
        tab.service("sheet")._set_name(window.lang, "Changé")
        assert tab.ctx.dirty
        tab.ctx.cancel()
        assert not tab.ctx.dirty and tab.ctx.draft["names"][window.lang] == "Trois plis mélèze"
        was = QMessageBox.question
        QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
        try:
            assert tab.ctx.delete_entry()
        finally:
            QMessageBox.question = was
        assert materials_user.find(mid) is None and not path.exists()


def test_the_window_says_valeurs_de_dimensionnement():
    """CON-002: the French words never say «valeurs de calcul»."""
    import materials_tab_words
    assert not [k for k, v in materials_tab_words.STRINGS["fr"].items() if "de calcul" in v.lower()]


def test_a_material_is_saved_in_a_project_open_read_only():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        was = window.read_only
        window.read_only = True
        try:
            assert tab.service("list").new_material("other")
            tab.service("sheet")._set_name(window.lang, "Lecture seule")
            assert tab.ctx.save_entry(), "the library is the engineer's, not the project's (UI-002)"
            from domains import materials_user
            assert any(m["names"].get(window.lang) == "Lecture seule" for m in materials_user.materials())
        finally:
            window.read_only = was


def test_an_unsaved_draft_is_kept_through_a_rebuild():
    window, here = _window()
    with project.using(here):
        tab = _tab(window)
        assert tab.service("list").new_material("panel")
        tab.service("sheet")._set_name(window.lang, "Trois plis brouillon")
        state = tab.view_state()
        import materials_tab
        again = materials_tab.MaterialsTab(window)
        again.restore(state)
        assert again.ctx.dirty and again.ctx.draft["names"][window.lang] == "Trois plis brouillon" and again.ctx.draft["type"] == "panel"
        again.ctx.cancel()
        tab.ctx.cancel()
