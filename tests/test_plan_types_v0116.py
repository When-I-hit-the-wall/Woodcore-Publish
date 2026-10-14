"""A position plan's type, the load-path plan's six load symbols, a section's load transfer levels and its storey boxes' STE designation (v0.116, plan-source 1.3; calc/domains/plan.py, plan_svg.py, calc/tools/plan_canvas.py, plan_tab.py, lib/calc-engine.typ's plan-figure; docs/domain/position-plans.md §3.3sexies).

The engineer, 06.10.2026: «dans le module plan … type de plan : coupe en plan qui permet d'afficher l'étage et le caractère de numérotation, ou alors coupe en élévation qui cache l'étage et le caractère de numérotation et qui change les outils … on doit également pouvoir cliquer sur plan de descente de charge» · «lorsque l'on a une coupe en élévation, dans les outils il faut un outil en plus … un niveau de reprise des charges … une ligne rouge avec une flèche verticale … à gauche et à droite» · «pour l'outil de cadre d'étage, il faut avoir au milieu du cadre d'étage la désignation comme dans la STE, donc x1xx … il ne faut pas avoir la désignation de l'étage en haut à gauche du rectangle»; and his answer 3: the load-path plan's tools are the position plan's plus STE Compact 02's six load symbols (pp. 14-15), numbered Pxxx / Lxxx.

What is held:

* a source of before 1.3 is read as it is, its type derived from its role; a stated type and the role must agree; a load symbol is refused outside a load-path plan and a load level outside a section;
* a load symbol is numbered by the plan -- P, the floor's character, the next two digits -- and is no position: it is in no list of positions, no warning about the project's positions and no `labels` of the export;
* a storey box's designation is «x» + its storey's numbering character + «xx», at the box's middle, the attic above the highest of the section's others; a storey with no character keeps its own name;
* a load level is a red dash-dot line, an arrow coming down onto each end and «Niveau de reprise des charges (x0xx)» beside it, in the language it is drawn in -- so a section carrying one is exported once per language and show-plan sets the report's;
* every load symbol is drawn, and listed in the legend in three languages;
* a plan that uses none of it is drawn and exported as it was (tests/test_plan_style.py holds the frozen hashes);
* in the window: «Type de plan» right under the ID switches the tools and hides the storey and the numbering character on a section; a load tool numbers what it draws; switching away from a load-path plan takes its loads out in one step of «Annuler»; the load level tool draws a level of the chosen storey; the list names a section and a load-path plan by their type.
"""

import contextlib
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata

import conftest
from conftest import ROOT, Skip
import project
import validation
from domains import plan
from domains import plan_svg

SAMPLE = ROOT / "tests" / "projet-exemple"


def _refused(source, words):
    try:
        plan.check_source(source, "P01.json")
    except validation.ValidationError as exc:
        assert words in str(exc), (words, str(exc))
    else:
        assert False, f"accepted: {words}"


def _loadpath(**extra):
    source = plan.new_source("LP1", floor="0")
    source["sheet"] = {"width": 1000.0, "height": 700.0}
    source["plan_type"] = "loadpath"
    source["elements"] = [
        {"type": "PL", "subtype": "vert", "label": "P001", "points": [[100, 100]]},
        {"type": "PL", "subtype": "horiz", "label": "P002", "points": [[300, 100]], "angle": 30},
        {"type": "PL", "subtype": "vh", "label": "P003", "points": [[500, 100]]},
        {"type": "LL", "subtype": "vert", "label": "L001", "points": [[100, 300], [400, 300]]},
        {"type": "LL", "subtype": "horiz", "label": "L002", "points": [[100, 400], [400, 400]]},
        {"type": "LL", "subtype": "vh", "label": "L003", "points": [[100, 500], [400, 500]]},
        {"type": "T", "label": "T001", "points": [[600, 300], [900, 300]]},
    ]
    source.update(extra)
    return source


def _section(**extra):
    source = plan.new_source("S01", floor="")
    source["sheet"] = {"width": 1000.0, "height": 700.0}
    source["role"] = "section"
    source["storey_boxes"] = [{"storey": "EG", "x": 100, "y": 300, "w": 700, "h": 150},
                              {"storey": "1.OG", "x": 100, "y": 150, "w": 700, "h": 150},
                              {"storey": "DG", "x": 100, "y": 50, "w": 700, "h": 100},
                              {"storey": "Mezzanine", "x": 100, "y": 460, "w": 700, "h": 40}]
    source["load_levels"] = [{"storey": "EG", "points": [[150, 460], [750, 460]]}]
    source.update(extra)
    return source


def _between(svg, opening, closing):
    return svg.split(opening)[1].split(closing)[0]


# --- the source ---------------------------------------------------------------------------------

def test_a_plans_type_is_derived_from_its_role_where_it_states_none():
    old = plan.new_source("P01")
    old["schema_version"] = "1.2"
    plan.check_source(old, "P01.json")
    assert plan.plan_type(old) == "floor"
    assert plan.plan_type({**old, "role": "section"}) == "section"
    assert plan.plan_type({**old, "plan_type": "loadpath"}) == "loadpath"
    assert plan.SOURCE_SCHEMA_VERSION == "1.6" and {"1.2", "1.3", "1.4", "1.5"} <= set(plan.SOURCE_SCHEMA_VERSIONS)   # 1.4 since v0.117, 1.5 since issue #9, 1.6 since issue #18
    plan.check_source(_loadpath(), "LP1.json")
    plan.check_source(_section(plan_type="section"), "S01.json")


def test_what_a_typed_source_may_not_say_is_refused_naming_it():
    _refused(_loadpath(plan_type="cellar"), "plan_type")
    _refused(_loadpath(plan_type="section"), "disagree")
    _refused(_section(plan_type="floor"), "disagree")
    _refused(_loadpath(plan_type="floor"), "load-path plan")
    floor = _section()
    floor["role"] = "plan"
    floor.pop("storey_boxes")
    _refused(floor, "load transfer levels are drawn on a section")
    _refused(_section(load_levels=[{"storey": "EG", "points": [[5, 5], [5, 5]]}]), "same point")
    _refused(_section(load_levels=[{"storey": " ", "points": [[0, 0], [10, 0]]}]), "names no storey")
    _refused(_section(load_levels=[{"storey": "EG", "points": [[0, 0], [10, 0]], "floor": "12"}]), "one character")
    _refused(_section(load_levels=[{"storey": "EG", "points": [[0, 0], [10, 0]], "style": {"line": 2}}]), "states none of its own")
    beam = _loadpath()
    beam["elements"][-1]["angle"] = 10
    _refused(beam, "no direction of its own")


def test_a_load_is_numbered_by_the_plan_and_is_no_position():
    source = _loadpath()
    assert plan.next_load_label(source, "PL") == "P004" and plan.next_load_label(source, "LL") == "L004"
    assert plan.next_load_label({"floor": "U", "elements": []}, "PL") == "PU01"
    assert plan.auto_label("LL", "1", [], ["L101"]) == "L101", "an empty plan: its first line load"
    # the loads are no positions: not shown as positions, not checked against the project's, not offered to paste
    assert plan.plan_labels(source) == ["T001"]
    assert plan.unknown_labels(source, []) == ["T001"]
    assert "P001" not in plan.missing_rows(source, []) and "L001" not in plan.missing_rows(source, [])
    codes = [(n.code, n.values.get("label")) for n in plan.warnings(source, ["T001"])]
    assert not [c for c in codes if c[1] and c[1][0] in "PL" and c[1] != "T001"], codes
    record = plan.build_record(source, (1000, 700))
    assert record["labels"] == ["T001"] and record["plan_type"] == "loadpath"
    assert [e["type"] for e in record["elements"]][:6] == ["PL"] * 3 + ["LL"] * 3 and record["elements"][1]["angle"] == 30


def test_the_storey_designation_is_x_its_numbering_character_xx():
    boxes = _section()["storey_boxes"]
    assert [plan.storey_designation(b, boxes) for b in boxes] == ["x0xx", "x1xx", "x2xx", "Mezzanine"]
    assert plan.storey_designation({"storey": "Mezzanine", "floor": "M"}) == "xMxx", "a character stated wins"
    assert plan.storey_designation({"storey": "2e SS"}) == "xUxx"


def test_a_quarter_turn_turns_the_load_levels_and_a_point_loads_direction():
    section = _section(load_levels=[{"storey": "EG", "points": [[150, 460], [750, 460]], "label_offset": [10, -5]}])
    turned = plan.rotate_source(section, 1, (1000, 700))
    assert turned["load_levels"][0]["points"] == [[240, 150], [240, 750]] and turned["load_levels"][0]["label_offset"] == [5, 10]
    loads = plan.rotate_source(_loadpath(), 1, (1000, 700))
    assert loads["elements"][1]["angle"] == 120
    back = plan.rotate_source(plan.rotate_source(plan.rotate_source(turned, 1, (700, 1000)), 1, (1000, 700)), 1, (700, 1000))
    assert back["load_levels"] == section["load_levels"]


# --- the drawing --------------------------------------------------------------------------------

def test_a_storey_boxs_designation_stands_at_its_middle_and_nothing_in_its_corner():
    section = _section()
    section.pop("load_levels")
    svg = plan_svg.render(section)
    inside = _between(svg, plan_svg.BOXES_OPEN, plan_svg.BOXES_CLOSE)
    texts = re.findall(r'<text x="([-\d.]+)" y="([-\d.]+)"[^>]*>([^<]+)</text>', inside)
    assert [t for _x, _y, t in texts] == ["x0xx", "x1xx", "x2xx", "Mezzanine"]
    sz = plan_svg.sizes_of(section)
    for (x, y, _t), box in zip(texts, section["storey_boxes"]):
        assert abs(float(x) - (box["x"] + box["w"] / 2)) < 1e-3, "centred across"
        assert abs(float(y) - 0.35 * sz.text(10) - (box["y"] + box["h"] / 2)) < 1e-2, "centred up and down"
    assert ">EG</text>" not in svg and ">1.OG</text>" not in svg, "the storey's own designation is written nowhere"
    assert svg.count("<rect") == inside.count("<rect") + 0, "a box around each designation, and no outline of the storey box itself"


def test_a_load_level_is_a_red_line_two_arrows_down_and_its_words_in_three_languages():
    section = _section()
    words = {"de": "Lastübergabeniveau (x0xx)", "fr": "Niveau de reprise des charges (x0xx)", "en": "Load transfer level (x0xx)"}
    for lang, text in words.items():
        svg = plan_svg.render(section, lang=lang)
        inside = _between(svg, plan_svg.LEVELS_OPEN, plan_svg.LEVELS_CLOSE)
        colour = plan_svg.LOAD_LEVEL_COLOUR
        assert f'stroke="{colour}"' in inside and "stroke-dasharray" in inside
        assert inside.count(f'<polygon') == 2 and inside.count(f'fill="{colour}"/>') == 2, "an arrowhead at each end"
        heads = re.findall(r'<polygon points="([^"]+)"', inside)
        tips = [tuple(float(v) for v in h.split()[0].split(",")) for h in heads]
        assert tips == [(150, 460), (750, 460)], "each arrow comes down onto an end of the line"
        assert f">{text}</text>" in inside, lang
    # moved clear of its line, a thin line runs back to it; brought back, none
    plain = _between(plan_svg.render(section), plan_svg.LEVELS_OPEN, plan_svg.LEVELS_CLOSE)
    moved = copy.deepcopy(section)
    moved["load_levels"][0]["label_offset"] = [0, -150]
    leader = _between(plan_svg.render(moved), plan_svg.LEVELS_OPEN, plan_svg.LEVELS_CLOSE)
    assert leader.count("<line") == plain.count("<line") + 1
    assert "Lastniveau" in plan_svg.legend_keys(section)


def test_every_load_symbol_is_drawn_and_listed_in_the_legend_in_three_languages():
    from i18n import strings
    source = _loadpath()
    svg = plan_svg.render(source)
    for index in range(6):
        group = svg.split(f'<g id="el-{index + 1}">')[1].split("</g>")[0]
        assert group.strip(), f"element {index + 1} drew nothing"
    for label, colour in (("P001", plan_svg.ORANGE), ("P002", plan_svg.VIOLET), ("P003", "#111111"),
                          ("L001", plan_svg.ORANGE), ("L002", plan_svg.VIOLET), ("L003", "#111111")):
        assert re.search(rf'fill="{colour}">{label}</text>', svg), label
    # a point load's number has its dotted line back to it, always
    assert svg.count('stroke-linecap="round"') >= 3
    keys = [item["key"] for item in plan_svg.legend_items(source)]
    assert keys == ["T", "PL:vert", "PL:horiz", "PL:vh", "LL:vert", "LL:horiz", "LL:vh"]
    for key in keys[1:] + ["Lastniveau"]:
        for lang in strings.LANGUAGES:
            assert strings.text(f"plan.legend.{key}", lang)
        assert plan_svg.legend_swatch(key).startswith("<svg") and plan_svg.swatch(*key.split(":")).count("<") >= 3
    assert strings.text("plan.legend.PL:vert", "fr") == "Charge ponctuelle verticale"


def test_a_plan_that_uses_none_of_it_is_drawn_and_exported_as_it_was():
    source = plan.new_source("P01")
    source["sheet"] = {"width": 1000.0, "height": 700.0}
    source["elements"] = [{"type": "S", "label": "S001", "points": [[600, 300]]}]
    record = plan.build_record(source, (1000, 700))
    assert not {"plan_type", "load_levels", "figures"} & set(record)
    assert plan_svg.render(source, lang="fr") == plan_svg.render(source)
    for marker in (plan_svg.BOXES_OPEN, plan_svg.LEVELS_OPEN):
        assert marker not in plan_svg.render(source)


# --- the export and the report ------------------------------------------------------------------

def _project(name):
    root = conftest.tmpdir(name) / "Exemple"
    shutil.copytree(SAMPLE, root, ignore=shutil.ignore_patterns("lib", "VERSION", "stamps", "_Archiv"))
    here = project.Project.load(root / "Exemple.woodcore")
    project.sync_engine(here)
    return here


def _write(here, source):
    (here.plans_dir / f"{source['id']}.json").write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _exported(name):
    here = _project(name)
    section = _section(id="S99", plan_type="section")
    section["load_levels"][0]["label_offset"] = [0, -60]
    loads = _loadpath(id="LP99")
    for source in (section, loads):
        _write(here, source)
        assert plan.read_source(here.plans_dir / f"{source['id']}.json") == source, "written and read back unchanged"
    positions = plan.known_positions(here.data_dir) + ["T001"]
    plan.export(here.plans_dir, here.root, here.data_dir, positions)
    return here


def test_a_section_with_a_load_level_is_exported_once_per_language():
    here = _exported("plan_types_export")
    data = json.loads((here.data_dir / "plans.json").read_text(encoding="utf-8"))
    validation.validate_structure(data, "plans")
    validation.validate_plans_business(data)
    record = data["plans"]["S99"]
    assert record["figures"] == {lang: f"plans/S99-{lang}.svg" for lang in ("de", "fr", "en")} and record["plan_type"] == "section"
    assert record["load_levels"][0]["designation"] == "x0xx" and record["load_levels"][0]["storey"] == "EG"
    assert "Niveau de reprise des charges (x0xx)" in (here.data_dir / "plans" / "S99-fr.svg").read_text(encoding="utf-8")
    assert (here.data_dir / "plans" / "S99.svg").read_text(encoding="utf-8") == (here.data_dir / "plans" / "S99-de.svg").read_text(encoding="utf-8")
    assert "figures" not in data["plans"]["LP99"] and data["plans"]["LP99"]["labels"] == ["T001"]
    # a figures entry of another shape is refused
    broken = copy.deepcopy(data)
    broken["plans"]["S99"]["figures"] = {"de": "plans/S99-de.svg"}
    try:
        validation.validate_plans_business(broken)
    except validation.ValidationError as exc:
        assert "de, fr and en" in str(exc)
    else:
        assert False, "a figure missing for two languages accepted"


def _text_of(pdf):
    from pypdf import PdfReader
    return unicodedata.normalize("NFKC", "\n".join(p.extract_text() for p in PdfReader(str(pdf)).pages))


def _run(here, body, name, lang):
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    d = here.typst_root / ".probe" / name
    d.mkdir(parents=True, exist_ok=True)
    probe = d / "probe.typ"
    probe.write_text('#import "/config.typ": conf\n#import "/commands.typ": *\n#show: conf\n'
                     f'#set-report-language("{lang}")\n' + body + "\n", encoding="utf-8")
    out = d / "probe.pdf"
    run = subprocess.run([project.typst_executable(), "compile", "--root", str(here.typst_root), str(probe), str(out)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr
    return _text_of(out)


def test_the_report_sets_the_level_in_its_language_and_the_loads_in_the_legend():
    here = _exported("plan_types_report")
    french = _run(here, '#show-plan("S99", caption: none)\n#show-plan-legend("LP99")', "fr", "fr")
    assert "Niveau de reprise des charges" in french and "Charge ponctuelle verticale" in french and "Charge linéaire horizontale" in french, french
    german = _run(here, '#show-plan("S99", caption: none)\n#show-plan-legend("LP99")', "de", "de")
    assert "Lastübergabeniveau" in german and "Punktlast vertikal" in german, german


def test_a_sheets_section_sets_a_section_drawn_once_per_language():
    """sheet-section stands in no context, which the per-language figure needs (plan-figure sets one itself)."""
    import sheets
    here = _exported("plan_types_sheet")
    sid = "SEC1"
    sheets.new_sheet(here, sid, "A3", True)
    sheets.add_section(here, sid, "S99", "EG", 20, 20, width=120)
    if not conftest.have_typst():
        raise Skip("typst is not on the path")
    ok, message = sheets.compile(here, sid)
    assert ok, message
    assert "x0xx" in _text_of(sheets.pdf(here, sid))


# --- the window ---------------------------------------------------------------------------------

_STATE = {}


def _qt():
    tools = str(ROOT / "calc" / "tools")
    if tools not in sys.path:
        sys.path.insert(0, tools)
    try:
        from PySide6.QtWidgets import QApplication
        import PySide6.QtPdf  # noqa: F401
    except ImportError as exc:
        raise Skip(f"PySide6 or its QtPdf is not installed ({exc})")
    return QApplication.instance() or QApplication([])


@contextlib.contextmanager
def _dialogs():
    from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox
    stubs = {
        (QMessageBox, "warning"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "critical"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "information"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok),
        (QMessageBox, "question"): staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes if len(a) < 4 else QMessageBox.StandardButton.Discard),
        (QFileDialog, "getOpenFileName"): staticmethod(lambda *a, **k: ("", "")),
        (QInputDialog, "getDouble"): staticmethod(lambda *a, **k: (2.5, True)),
    }
    originals = {key: key[0].__dict__[key[1]] for key in stubs}
    for (owner, attr), stub in stubs.items():
        setattr(owner, attr, stub)
    try:
        yield
    finally:
        for (owner, attr), original in originals.items():
            setattr(owner, attr, original)


def _tab():
    if "window" not in _STATE:
        app = _qt()
        here = conftest.project_copy("plan_types_v0116")
        with project.using(here), _dialogs():
            import woodcore_gui
            window = woodcore_gui.MainWindow()
        _STATE.update(app=app, window=window, here=here)
    tab = next(t for t in _STATE["window"].tabs if type(t).__name__ == "PlanTab")
    tab.dirty = False
    return tab, _STATE["here"]


def _open(tab, source):
    tab.open_source(source, None, False)
    tab.show_plan_view()
    tab.canvas.select(None)
    tab.dirty = False


def _shown(tab, tool):
    return not tab.tool_buttons[tool].isHidden()


def test_the_plan_type_switches_the_tools_and_the_storey_rows():
    tab, here = _tab()
    with project.using(here), _dialogs():
        source = plan.new_source("P98", floor="0")
        _open(tab, source)
        form = tab.plan_form
        assert form.itemAt(tab.plan_type_row, form.ItemRole.FieldRole).widget() is tab.plan_type_combo, "right under the ID"
        assert [tab.plan_type_combo.itemData(i) for i in range(3)] == ["floor", "section", "loadpath"]
        assert _shown(tab, "V") and not _shown(tab, "PL") and tab.section_row.isHidden()
        assert form.isRowVisible(tab.storey_combo) and form.isRowVisible(tab.floor_edit)
        tab.plan_type_combo.setCurrentIndex(1)
        assert source["plan_type"] == "section" and source["role"] == "section"
        assert not tab.section_row.isHidden() and not _shown(tab, "V") and not _shown(tab, "PL")
        assert not form.isRowVisible(tab.storey_combo) and not form.isRowVisible(tab.floor_edit), "a section hides the storey and the numbering character"
        tab.choose_tool("V")
        assert tab.canvas.tool == "select", "an STE tool is no section's"
        tab.plan_type_combo.setCurrentIndex(2)
        assert source["plan_type"] == "loadpath" and source["role"] == "plan"
        assert _shown(tab, "V") and _shown(tab, "PL") and _shown(tab, "LL") and tab.section_row.isHidden()
        assert form.isRowVisible(tab.storey_combo) and form.isRowVisible(tab.floor_edit)
        assert tab.entry_text("P98", source) == f"P98 · {tab.t('plan_kind_short_loadpath')}"
        assert tab.entry_text("P97", plan.new_source("P97")) == "P97"
        tab.dirty = False


def test_a_load_tool_numbers_what_it_draws_and_leaving_the_type_takes_the_loads_out():
    tab, here = _tab()
    with project.using(here), _dialogs():
        source = plan.new_source("P96", floor="0")
        source["plan_type"] = "loadpath"
        _open(tab, source)
        tab.choose_tool("PL")
        tab.canvas.place((200.0, 200.0))
        tab.canvas.place((260.0, 200.0))
        tab.choose_tool("LL")
        tab.canvas.place((100.0, 300.0))
        tab.canvas.place((400.0, 300.0))
        tab.canvas.finish_drawing()
        labels = [(e["type"], e["label"]) for e in source["elements"]]
        assert labels == [("PL", "P001"), ("PL", "P002"), ("LL", "L001")], labels
        plan.check_source(source, "P96.json")
        # the card of a load: its number free, a horizontal point load's direction -- with «Sélection»: while a drawing tool is chosen the pane is the tool's (issue #9, D-014)
        tab.choose_tool("select")
        tab.canvas.select(("element", 0))
        tab.set_subtype("horiz")
        tab.refresh_selection()
        from PySide6.QtWidgets import QDoubleSpinBox, QLineEdit
        assert any(w.text() == "P001" for w in tab.selection_group.findChildren(QLineEdit))
        assert tab.selection_group.findChildren(QDoubleSpinBox), "a horizontal point load has a direction"
        tab.set_load_label("PU07")
        assert source["elements"][0]["label"] == "PU07"
        # back to a floor plan: the loads go, in one step of «Annuler»
        tab.canvas.select(None)
        tab.plan_type_combo.setCurrentIndex(0)
        assert not [e for e in source["elements"] if plan.is_load(e["type"])]
        tab.undo()
        assert len([e for e in tab.source["elements"] if plan.is_load(e["type"])]) == 3
        tab.dirty = False


def test_the_load_level_tool_draws_a_level_of_the_storey_chosen():
    tab, here = _tab()
    with project.using(here), _dialogs():
        source = plan.new_source("S98", floor="")
        source["sheet"] = {"width": 1000.0, "height": 700.0}
        source["plan_type"] = "section"
        source["role"] = "section"
        _open(tab, source)
        assert _shown(tab, "load-level")
        tab.storey_choice.setEditText("EG")
        tab.choose_tool("load-level")
        assert tab.hint.text() == tab.t("plan_hint_load_level")
        tab.canvas.place((150.0, 460.0))
        tab.canvas.place((750.0, 460.0))
        level = source["load_levels"][0]
        assert level["storey"] == "EG" and level["floor"] == "0" and level["points"] == [[150, 460], [750, 460]]
        assert tab.canvas.selection == ("load-level", 0) and tab.has_selection()
        plan.check_source(source, "S98.json")
        # its card: what it is, its storey and its numbering character, which may be written over
        tab.refresh_selection()
        from PySide6.QtWidgets import QLineEdit
        fields = [w for w in tab.selection_group.findChildren(QLineEdit) if w.maxLength() == 1]
        assert fields and fields[0].text() == "0"
        tab.set_entry_floor(level, "U")
        assert level["floor"] == "U"
        assert "(xUxx)" in plan_svg.render(source, lang="fr")
        # the words are taken by a click and moved; Suppr deletes the level
        frame = dict(tab.canvas.load_level_frames())[0]
        tab.canvas.select(None)
        tab.choose_tool("select")
        tab.canvas.press_select(frame["at"])
        assert tab.canvas.drag and tab.canvas.drag["kind"] == "load-level-label"
        tab.canvas.drag = None
        tab.canvas.delete_selection()
        assert source["load_levels"] == []
        tab.dirty = False
