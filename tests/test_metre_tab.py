"""The «Métré» tab under «Positions» (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, UI-003, Q-003; calc/tools/metre_tab.py): the export's quantities, never measured in the window, their date and a banner when a plan is newer, and the file of the list (Q-008)."""

TIER = "fast"  # tests/run_tests.py --fast

import os
import time

import conftest
import project
import test_positions_tab as base


def _metre(window):
    import metre_tab
    return next(t for t in window.tabs if isinstance(t, metre_tab.MetreTab))


def test_the_tab_shows_the_export_s_quantities_by_scope_and_measures_nothing():
    """UI-003: the table is `quantities.summary` of data/quantities.json's rows -- everything drawn, one plan, chosen positions --; a plan drawn after the export changes nothing in the tab until the export writes it again, and the banner says it."""
    from domains import plan, quantities
    import positions_store as store
    window, here = base._window()
    with project.using(here), base._boxes():
        base._drawn(here)
        tab = _metre(window)
        quantities.write_document(here)
        tab.on_shown()
        assert tab.banner.isHidden() and "quantities.json" in tab.exported.text()
        found, _notes = quantities.rows(plan.position_plan_sources(here.plans_dir), store.read(here))

        def table():
            return [[item.text(c) for c in range(5)] for item in (tab.table.topLevelItem(i) for i in range(tab.table.topLevelItemCount()))]

        groups, _totals = quantities.summary(found, "all")
        tab.scope_combo.setCurrentIndex(tab.scope_combo.findData("all"))
        assert any(row[0] == groups[0]["material"] and row[3] == quantities.metres(groups[0]["length_m"]) for row in table()), (table(), groups)
        tab.scope_combo.setCurrentIndex(tab.scope_combo.findData("plans"))
        tab.plan_combo.setCurrentIndex(tab.plan_combo.findData("EG"))
        eg_groups, _ = quantities.summary(found, "plans", plans=["EG"])
        assert any(row[0] == eg_groups[0]["material"] and row[3] == quantities.metres(eg_groups[0]["length_m"]) for row in table()), table()
        tab.scope_combo.setCurrentIndex(tab.scope_combo.findData("positions"))
        tab.position_list.clearSelection()
        assert table() == [] and tab.note.text() == tab.t("mt_none_selected")
        next(tab.position_list.item(i) for i in range(tab.position_list.count()) if tab.position_list.item(i).text() == "S001").setSelected(True)
        assert table() and all(row[3] in ("—", "") for row in table()), table()   # a column: a piece, no length
        # a plan saved after the export: the tab still shows the export, and says it is out of date
        before = table()
        source = here.plans_dir / "EG.json"
        later = (here.data_dir / "quantities.json").stat().st_mtime + 5
        os.utime(source, (later, later))
        tab.on_shown()
        assert not tab.banner.isHidden() and "EG" in tab.banner.text() and table() == before
        quantities.write_document(here)
        os.utime(here.data_dir / "quantities.json", (later + 5, later + 5))
        tab.on_shown()
        assert tab.banner.isHidden()
        tab.scope_combo.setCurrentIndex(tab.scope_combo.findData("all"))


def test_the_tab_writes_its_file_once_and_offers_the_rows_it_misses():
    """Q-008: «Écrire le fichier» writes Positions/quantities.typ once, «Ajouter» is offered for a row of the export the file does not hold, «Copier l'inclusion» copies the `#include` a section prints it with."""
    from PySide6.QtWidgets import QApplication
    from domains import list_files, quantities
    window, here = base._window()
    with project.using(here), base._boxes():
        tab = _metre(window)
        target = list_files.path(here, "quantities")
        if target.exists():
            target.unlink()
        quantities.write_document(here)
        tab.on_shown()
        card = tab.file_card
        assert card.write_button.isVisibleTo(tab) or not tab.isVisible()
        card.write()
        assert target.is_file() and list_files.missing(here, "quantities") == []
        assert not card.add_button.isEnabled()
        card.copy()
        assert QApplication.clipboard().text() == f'#include "{here.from_root(target)}"'
        base._drawn(here)
        quantities.write_document(here)
        card.refresh()
        if list_files.missing(here, "quantities"):
            assert card.add_button.isEnabled()
            card.add()
            assert list_files.missing(here, "quantities") == []
