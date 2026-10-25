"""The «Domaines» tab off-screen -- its frame, its list, its modes, its domains' names and IDs, its folders and archives, its «Affichage», an unfolded check (calc/tools/formula_tab.py, formula_tab_domains.py, formula_tab_unfold.py; issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, UI-001 to UI-004, UI-020 to UI-022, REQ-004, REQ-015, REQ-018, ARCH-009, ARCH-013; issue #15 before it).

Held: the tab is in *Référence*, first, «Domaines / Domänen / Domains», its writers refused read only; three views, Formulaire · Code · Affichage, no pill painted; the list holds the domains with their state and never unfolds them, the specialised tabs' groups folded, no Typst in it; the centre names the domain, its ID, its file; the right pane holds the five modules in their order; a new domain is named on its first line, its ID made from it, written on Enter with `#calc-defaults(presets: "block")`; an ID changed renames the file and lists what still cites it; folders, order, duplicate, archives kept in lists.json; a file changed on the disk is never written over; «Affichage» compiles the engineer's file, writes a level and a domain's option into it and never the base of unfold; an unfolded check colours its rows by their states; `open_object("formula:<id>")` opens the domain.
"""

import json
import shutil
import sys

import conftest
from conftest import ROOT, Skip

import list_order
import project
from domains import formula_domain as fd
from domains import unfold

TOOLS = ROOT / "calc" / "tools"
FIXTURE = ROOT / "tests" / "fixtures" / "domains" / "panne-p2.typ"
_STATE = {}


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _tab():
    if "tab" not in _STATE:
        _qt()
        import woodcore_gui
        import formula_tab
        window = woodcore_gui.MainWindow()
        tab = next(t for t in window.tabs if isinstance(t, formula_tab.FormulaTab))
        _STATE.update(window=window, tab=tab)
    return _STATE["window"], _STATE["tab"]


def _pump():
    from PySide6.QtWidgets import QApplication
    for _ in range(3):
        QApplication.processEvents()


def _cleanup(tab, name):
    here = project.current()
    for domain in fd.list_domains(here):
        if domain.name == name:
            fd.remove(here, domain)
    tab.reload(keep="")


def _new(tab, name):
    _cleanup(tab, name)
    tab.new_domain()
    tab.name_edit.setText(name)
    tab.name_done()
    return project.current().formulas_dir / f"{tab.current_id}.typ"


def _type(tab, text):
    """A line typed at the foot of the form and written by Enter."""
    foot = tab.form.foot
    foot.text.setText(text)
    foot.refresh()
    foot.commit()
    _pump()


def _said(tab):
    said = []
    tab.fail = lambda message: said.append(message) or False
    return said


def test_the_tab_is_first_in_reference_in_three_languages_its_writers_guarded():
    """UI-001, UI-023, ARCH-013: «Domaines / Domänen / Domains», first in Référence, with its icon, its words in three languages; every writer it defines refused in a project opened read-only."""
    _qt()
    import chrome
    import formula_tab
    import woodcore_gui
    assert dict(woodcore_gui.NAV_GROUPS)["nav_reference"][0] == "tab_formula" and "tab_formula" in chrome.ICONS
    words = [set(formula_tab.STRINGS[lang]) for lang in ("fr", "de", "en")]
    assert words[0] == words[1] == words[2], sorted(words[0] ^ words[1] | words[0] ^ words[2])
    assert [woodcore_gui.STRINGS[lang]["tab_formula"] for lang in ("fr", "de", "en")] == ["Domaines", "Domänen", "Domains"]
    assert not [k for lang in ("fr", "de", "en") for k, v in formula_tab.STRINGS[lang].items() if "var-domain" in v], "a word still names #var-domain (UI-023)"
    for retired in ("fm_cmd_val", "fm_cmd_var-unit"):
        assert retired not in formula_tab.STRINGS["fr"], retired
    own = {k: v for c in reversed(woodcore_gui.own_classes(formula_tab.FormulaTab)) for k, v in vars(c).items()}
    for name in woodcore_gui.WRITERS:
        if name in own:
            assert hasattr(getattr(formula_tab.FormulaTab, name), "__wrapped__"), f"FormulaTab.{name} is not refused in a project opened read-only"
    for name in ("save", "delete", "duplicate_domain", "rename_id", "write_field", "write_new_line", "write_delete_rows", "write_undo", "write_move_rows",
                 "write_links", "write_argument", "write_code", "write_domain_option", "write_domain_level", "write_line_display", "write_reset_line"):
        assert name in woodcore_gui.WRITERS and name in own, name


def test_three_modes_and_no_pill():
    """UI-001, ARCH-004: the tab declares Formulaire · Code · Affichage, in this order; no pill, no text-with-pills module is left (ARCH-005)."""
    import importlib.util
    _window, tab = _tab()
    import views
    assert tab.VIEWS == ("form", "code", "display") and views.default(tab) == "form"
    assert [key for key, _n, _t in views.items(tab, tab.t)] == ["form", "code", "display"]
    for gone in ("formula_tab_widgets", "formula_tab_blocks"):
        assert importlib.util.find_spec(gone) is None, gone
    assert not (ROOT / "calc" / "domains" / "formula_layout.py").exists()
    tab.set_view("code")
    assert tab.work.currentWidget() is tab.code
    tab.set_view("form")
    assert tab.work.currentWidget() is tab.form


def test_the_list_holds_the_domains_folded_with_their_state_and_no_typst():
    """UI-002, defect 7: a domain is one row, never unfolded line by line; its state after its name; the groups of the specialised tabs folded; no row writes Typst."""
    _window, tab = _tab()
    tab.reload(keep="poutre-p1")
    import grouped_list
    item = tab.list._item_for("poutre-p1")
    assert item is not None and item.childCount() == 0 and item.text(0).startswith("Poutre P1") and "70 %" in item.text(0)
    texts = []
    for i in range(tab.list.topLevelItemCount()):
        top = tab.list.topLevelItem(i)
        texts.append(top.text(0))
        if top.data(0, grouped_list.KIND_ROLE) == "folder":
            assert not top.isExpanded(), f"the group {top.text(0)} is unfolded"
            texts += [top.child(j).text(0) for j in range(top.childCount())]
    assert not [t for t in texts if '_("' in t], texts
    first = tab.list.topLevelItem(0)
    assert first.data(0, grouped_list.KIND_ROLE) == "leaf", "the tab's own domains come before the groups (UI-002)"


def test_the_centre_names_the_domain_and_the_right_holds_five_modules():
    """UI-003, UI-004: the name, the ID and the file of Panne P2; the legend of the hovers; État du domaine, Arguments de la ligne, Résultats, Variables du domaine, in this order."""
    _window, tab = _tab()
    here = project.current()
    shutil.copy(FIXTURE, here.formulas_dir / "panne-p2.typ")
    try:
        tab.reload(keep="panne-p2")
        assert tab.name_edit.text() == "Panne de toiture P2" and tab.id_edit.text() == "panne-p2" and tab.file_label.text() == "Domains/panne-p2.typ"
        assert tab.t("fm_legend_uses") in tab.legend.text()
        fixed = [m for m in tab.pane.order if m not in tab.pane.pins]
        assert fixed[:4] == ["state", "args", "results", "variables"], fixed
    finally:
        (here.formulas_dir / "panne-p2.typ").unlink()
        tab.reload(keep="")


def test_a_domain_is_named_its_id_made_from_it_and_written_in_a_block():
    """REQ-004 of issue #15, D-3: a new domain named on its first line, its ID made from the name until written, written on Enter -- with `#calc-defaults(presets: "block", scope: "domain")`; a name changed then renames nothing."""
    _window, tab = _tab()
    _cleanup(tab, "Essai A")
    tab.new_domain()
    assert tab.current_id is None
    tab.name_edit.setText("Essai A")
    tab.name_typed("Essai A")
    assert tab.id_edit.text() == "essai-a"
    tab.name_done()
    path = project.current().formulas_dir / "essai-a.typ"
    text = path.read_text(encoding="utf-8")
    assert tab.current_id == "essai-a" and '#domain("essai-a", label: "Essai A")[' in text
    assert '#calc-defaults(presets: "block", scope: "domain")' in text, text
    tab.name_edit.setText("Essai A bis")
    tab.name_done()
    assert tab.current_id == "essai-a" and fd.read(path).name == "Essai A bis"
    _cleanup(tab, "Essai A bis")


def test_an_id_changed_renames_the_file_and_one_that_is_no_id_is_refused():
    """Issue #15, REQ-004: an ID that is no ID, or another domain's, refused; a new one renames the file, its place and folder in lists.json following it, what cites the old one listed."""
    _window, tab = _tab()
    path = _new(tab, "Essai I")
    _type(tab, "F = 5 kN")
    old_id = tab.current_id
    tab.list.drop_ids([old_id], None, "Essais")
    section = project.current().typst_root / "probe-cite.typ"
    section.write_text(f'#include "/Domains/{old_id}.typ"\n', encoding="utf-8")
    import notices_ui
    told = []
    saved_tell = notices_ui.tell
    notices_ui.tell = lambda message, *a, **k: told.append(message)
    said = _said(tab)
    try:
        tab.id_edit.setText("Essai I")
        tab.id_done()
        assert said and "Essai I" in said[0] and path.is_file(), said
        tab.id_edit.setText("poutre-p1")
        tab.id_done()
        assert "poutre-p1" in said[-1] and path.is_file(), said
        tab.id_edit.setText("essai-i2")
        tab.id_done()
    finally:
        notices_ui.tell = saved_tell
        del tab.fail
        section.unlink(missing_ok=True)
    new = project.current().formulas_dir / "essai-i2.typ"
    assert tab.current_id == "essai-i2" and new.is_file() and not path.exists()
    groups = list_order.tab_of(list_order.read(project.current()), tab.KEY)[1]
    assert groups.get("essai-i2") == "Essais"
    tab.app.list_store.forget(tab.KEY, ["essai-i2"])
    assert told and "probe-cite.typ:1" in told[0], told
    _cleanup(tab, "Essai I")


def test_folders_order_duplicate_and_archives():
    """Issue #15, REQ-008, REQ-009: a domain filed in a folder (lists.json, its file untouched), duplicated beside itself, archived and restored."""
    _window, tab = _tab()
    here = project.current()
    first = _new(tab, "Essai M")
    first_id = tab.current_id
    stamp = first.stat().st_mtime_ns
    tab.list.drop_ids([first_id], None, "Toiture")
    assert list_order.tab_of(list_order.read(here), tab.KEY)[1].get(first_id) == "Toiture" and first.stat().st_mtime_ns == stamp
    assert tab.duplicate_domain()
    copy_id = tab.current_id
    assert copy_id != first_id and list_order.tab_of(list_order.read(here), tab.KEY)[1].get(copy_id) == "Toiture"
    from PySide6.QtWidgets import QMessageBox
    saved = QMessageBox.question
    QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
    try:
        tab.archive.archive([copy_id])
    finally:
        QMessageBox.question = saved
    assert not (here.formulas_dir / f"{copy_id}.typ").exists()
    key = next(k for k in tab.list.archived_ids() if copy_id in k)
    tab.archive.restore([key], "")
    assert (here.formulas_dir / f"{copy_id}.typ").is_file()
    for name in ("Essai M", tab.t("fm_copy", name="Essai M")):
        _cleanup(tab, name)
    tab.app.list_store.forget(tab.KEY, [first_id, copy_id])


def test_a_file_changed_on_the_disk_is_never_written_over():
    """A line written elsewhere while the tab held the domain: the tab's next write refused and said, the domain read again as the file now is."""
    _window, tab = _tab()
    import notices_ui
    path = _new(tab, "Essai D")
    _type(tab, "F = 5 kN")
    elsewhere = path.read_text(encoding="utf-8").replace('#var("F", 5, "kN")', '#var("F", 5, "kN")\n  #var("G", 2, "m")')
    path.write_text(elsewhere, encoding="utf-8", newline="")
    told = []
    saved_tell = notices_ui.tell
    notices_ui.tell = lambda message, *a, **k: told.append(message)
    try:
        _type(tab, "H = 3 m")
    finally:
        notices_ui.tell = saved_tell
    assert path.read_text(encoding="utf-8") == elsewhere
    assert any(path.name in m for m in told), told
    assert [c.key for c in tab.domain.commands if c.defines] == ["F", "G"]
    _cleanup(tab, "Essai D")


def test_the_index_is_rewritten_at_every_write_under_the_domain_s_id():
    """REQ-010 of issue #15: a line written, the index the «Variables» tab reads written at once, the domain under its id."""
    _window, tab = _tab()
    _new(tab, "Essai O")
    _type(tab, "F = 5 kN")
    data = json.loads((project.current().data_dir / fd.EXPORT_FILE).read_text(encoding="utf-8"))
    assert data["domains"][tab.current_id] == {"title": "Essai O", "file": f"Domains/{tab.current_id}.typ"}
    _cleanup(tab, "Essai O")


def test_affichage_compiles_the_engineer_s_file_and_writes_into_it_never_the_base():
    """UI-020, UI-021, ARCH-009: «Affichage» is the snow's view on `Domains/<id>.typ` -- the command to copy its `#include`, «lire une valeur ailleurs», the domain's options --; ticking `presets: "block"` writes the line under the header, a line's own level set then given back writes and takes out `level:`, the domain's level is written into its header; the base of unfold is never written."""
    _window, tab = _tab()
    here = project.current()
    path = _new(tab, "Essai E")
    _type(tab, "F = 5 kN")
    _type(tab, "M = F * 2")
    base = here.data_dir / "unfold-base.json"
    was = base.read_text(encoding="utf-8") if base.is_file() else None
    tab.set_view("display", enter=False)
    try:
        tab.update_display(force=True)
        view = tab.display
        assert view.command() == f'#include "/Domains/{tab.current_id}.typ"'
        assert view.source().rstrip().endswith("]") and "#calc-defaults" in view.source()
        assert tab.display.src.read_call == f'#var("M", domain: "{tab.current_id}", display: "value-unit")'
        assert [e["id"] for e in view.elements[1:]] == ["var:1", "eq:2"]
        tab.write_domain_option("presets", None)
        assert "#calc-defaults" not in path.read_text(encoding="utf-8")
        tab.write_domain_option("presets", "block")
        lines = path.read_text(encoding="utf-8").split("\n")
        assert lines[3] == '#calc-defaults(presets: "block", scope: "domain")', lines
        tab.write_line_display("eq:2", {"level": 2})
        assert 'level: 2' in path.read_text(encoding="utf-8")
        tab.write_line_display("eq:2", {"level": None})
        assert 'level:' not in path.read_text(encoding="utf-8")
        tab.write_domain_level(3)
        assert f'#domain("{tab.current_id}", label: "Essai E", level: 3)[' in path.read_text(encoding="utf-8")
        tab.write_domain_level(None)
        assert ", level:" not in path.read_text(encoding="utf-8")
        tab.write_argument(2, "display-formula", "value")
        assert 'display-formula: "value"' in path.read_text(encoding="utf-8")
        tab.write_reset_line(2)
        assert "display-formula" not in path.read_text(encoding="utf-8")
    finally:
        tab.set_view("form", enter=False)
    assert (base.read_text(encoding="utf-8") if base.is_file() else None) == was, "the base of unfold was written"
    _cleanup(tab, "Essai E")


def test_a_domain_that_does_not_compile_says_one_message():
    """UI-022: a file Typst would not compile shows the state's fault, at Typst's line and column, once."""
    _window, tab = _tab()
    import formula_display
    here = project.current()
    text = FIXTURE.read_text(encoding="utf-8").replace('label: "Hauteur")', 'label: "Hauteur"')
    (here.formulas_dir / "panne-p2.typ").write_text(text, encoding="utf-8")
    try:
        tab.reload(keep="panne-p2")
        assert tab.domain.state == "unreadable"
        messages = [tab.say(m) for m in tab.state.errors]
        assert messages == [tab.t("fm_e_read_unclosed", line=19, col=6)], messages
        assert formula_display.failure_text(tab.t, messages, "error: unclosed delimiter") == messages[0]
    finally:
        (here.formulas_dir / "panne-p2.typ").unlink()
        tab.reload(keep="")


def test_open_object_opens_a_domain_of_the_tab():
    """REQ-018: the node `formula:<id>` of the graph opens the domain here -- what «Ouvrir l'onglet» of the «Variables» tab does."""
    window, tab = _tab()
    tab.reload(keep="")
    assert tab.GRAPH_KIND == "formula" and tab.lists_object("poutre-p1") and not tab.lists_object("nothing")
    assert window.open_object("formula:poutre-p1") and tab.current_id == "poutre-p1"


def test_an_unfolded_check_colours_its_rows_and_imports_them():
    """REQ-015, ARCH-RISK-018 (spec 2026-10-15, UI-002): a domain unfolded from a check keeps its card and its actions, and each line out of step colours its row -- `local` orange, `own` the accent, `conflict` red."""
    from domains import member_check, formula_state
    _window, tab = _tab()
    here = project.current()
    path = unfold.domain_path(here, "ZT-01")
    with project.using(here):
        member_check.export(here)
    try:
        path.write_text(path.read_text(encoding="utf-8").replace("`N_t_d / A`", "`N_t_d / (A)`"), encoding="utf-8")
        tab.reload(keep="ZT-01")
        _pump()
        assert not tab.unfold_card.isHidden()
        sigma = next(i for i, c in enumerate(tab.domain.commands) if c.key == "sigma_t_0_d")
        row = tab.form.row_of(sigma)
        assert row.state == "local" and formula_state.COLOURS["local"] == "warning"
        assert row.message.text() == tab.t("fm_unfold_state_local"), "the stripe without its word"
        assert tab.write_unfold_import_all() is True
        sigma = next(i for i, c in enumerate(tab.domain.commands) if c.key == "sigma_t_0_d")
        assert tab.form.row_of(sigma).state is None
    finally:
        path.unlink(missing_ok=True)
        base = unfold.read_base(here)
        base["domains"].pop("ZT-01", None)
        unfold.write_base(here, base)
        tab.reload(keep="")
