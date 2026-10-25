"""The «Métré» tab under «Positions» (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, UI-003, Q-003; calc/tools/metre_tab.py): the export's quantities, never measured in the window, their date and a banner when a plan is newer, and the file of the list (Q-008)."""

TIER = "fast"  # tests/run_tests.py --fast

import os
import time

import conftest
import project
import test_positions_tab as base


def _metre(window):
    """The tab's browser (issue #106: the tab is a class of parameters on the type «Données», its content one whole service); its banner is the type's, `_banner`."""
    import metre_tab
    return next(t for t in window.tabs if isinstance(t, metre_tab.MetreTab)).service("browser")


def _banner(tab):
    return tab.ctx.host.service("banner").label


def test_the_tab_shows_the_export_s_quantities_by_scope_and_measures_nothing():
    """UI-003: the table is `quantities.summary` of data/quantities.json's rows -- everything drawn, one plan, chosen positions --; a plan drawn after the export changes nothing in the tab until the export writes it again, and the banner says it."""
    from domains import plan, quantities
    import positions_store as store
    window, here = base._window()
    with project.using(here), base._boxes():
        base._drawn(here)
        tab = _metre(window)
        quantities.write_document(here)
        tab.shown()
        assert _banner(tab).isHidden() and "quantities.json" in tab.exported.text()
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
        tab.shown()
        assert not _banner(tab).isHidden() and "EG" in _banner(tab).text() and table() == before
        quantities.write_document(here)
        os.utime(here.data_dir / "quantities.json", (later + 5, later + 5))
        tab.shown()
        assert _banner(tab).isHidden()
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
        tab.shown()
        card = tab.file_card
        assert card.write_button.isVisibleTo(tab.widget) or not tab.widget.isVisible()
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


def test_the_file_card_writes_nothing_in_a_project_open_read_only():
    """REQ-010 of the spec 2026-10-24-type-donnees (issue #106, D-09): the card of a list written once -- «Métrés»'s, «Journal»'s, «Positions»' -- is guarded where it is defined: in a project another window holds, «Écrire le fichier» and «Ajouter» are refused with the window's one message and write nothing."""
    from domains import list_files
    base._qt()
    import list_file_card
    import tab_registry  # noqa: F401  -- the guards are set as the registry is read

    class ReadOnly:
        read_only = True

        def __init__(self):
            self.refused, self.said = 0, []

        def t(self, key, **values):
            return key

        def refuse_read_only(self):
            self.refused += 1

        def set_status(self, text):
            self.said.append(text)

    here = conftest.project_copy("metre_read_only")
    with project.using(here):
        for kind, document in (("quantities", lambda: "rs"), ("journal", lambda: "rs")):
            app = ReadOnly()
            card = list_file_card.ListFileCard(app, kind, document)
            target = list_files.path(here, kind, "rs")
            assert not target.exists()
            assert card.write() is False and card.add() is False, kind
            assert app.refused == 2 and not app.said and not target.exists(), (kind, app.refused, app.said)


def test_the_tab_keeps_its_scope_through_a_rebuild():
    """Issue #106 (REQ-007 of the spec 2026-10-24-type-donnees): the tab on the type «Données» keeps the scope, the plan and the positions chosen through a rebuild of itself (the browser's `state`, given back by the frame)."""
    window, here = base._window()
    with project.using(here), base._boxes():
        tab = _metre(window)
        tab.scope_combo.setCurrentIndex(tab.scope_combo.findData("positions"))
        if tab.position_list.count():
            tab.position_list.item(0).setSelected(True)
        chosen = tab.chosen_positions()
        new = window.refresh_tab("tab_metre").service("browser")
        assert new.scope_combo.currentData() == "positions" and new.chosen_positions() == chosen
        new.scope_combo.setCurrentIndex(new.scope_combo.findData("all"))
