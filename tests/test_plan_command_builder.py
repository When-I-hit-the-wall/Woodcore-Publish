"""The «Commande Typst» entry of the position-plan tab (v0.114, calc/tools/plan_command_builder.py): every option of `#show-plan` as a control, the call they say, and the page that call prints compiled live.

The command is a pure function of the options (`command_text`, over `build_reference.call_show_plan`), so most of what is held here needs no window: the defaults write nothing, each option writes only what differs from `show-plan`'s own, a detail without a highlighted position is no detail. The controls are driven off-screen, and one real compile of the snippet against a project made by `project_template.create` -- given the example project's export -- says that what the preview asks Typst for compiles and shows the plan.
"""

import io
import os
import shutil
import sys
import time

import conftest
from conftest import Skip

TOOLS = conftest.CALC / "tools"
PLANS = {
    "P01": {"labels": ["T001", "S001", "S002"], "scale": {"mode": "ratio", "units_per_m": 100.0, "ratio": 50}},
    "P02": {"labels": ["T003"]},
}


def _qt():
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    try:
        from PySide6.QtWidgets import QApplication
        import PySide6.QtPdfWidgets  # noqa: F401
    except ImportError as exc:
        raise Skip(f"PySide6 or its QtPdfWidgets is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _options(lang="en"):
    _qt()
    import plan_command_builder as pcb
    options = pcb.CommandOptions(lang)
    options.set_plans(PLANS)
    return pcb, options


def _tick(options, *labels):
    from PySide6.QtCore import Qt
    for i in range(options.positions.count()):
        item = options.positions.item(i)
        item.setCheckState(Qt.CheckState.Checked if item.data(Qt.ItemDataRole.UserRole) in labels else Qt.CheckState.Unchecked)


def test_the_defaults_write_the_bare_call_and_each_option_only_what_differs():
    _qt()
    import plan_command_builder as pcb
    # a native figure of the report's own since the spec 2026-10-21-commandes-typst-refonte (REQ-013, ARCH-012): what is drawn and set under it in the vocabulary's words, only what differs from the defaults
    assert pcb.command_text({"plan": "P01"}) == '#figure(image-positions-plan("P01"), kind: image, caption: [P01]) <fig-p01>'
    assert pcb.command_text({"plan": "P01", "width": "60%", "legend": False, "axes": False, "scale_bar": False}) == \
        '#figure(image-positions-plan("P01", detail-figure: ("length", "dimensions", "centres"), detail-legend: "none", width: 60%), kind: image, caption: [P01]) <fig-p01>'
    assert pcb.command_text({"plan": "P01", "highlight": ["T001"]}) == '#figure(image-positions-plan("P01", highlight: "T001"), kind: image, caption: [P01]) <fig-p01>'
    assert pcb.command_text({"plan": "P01", "highlight": ["T001", "S001"], "detail": True, "zoom": 1.5}) == \
        '#figure(image-positions-plan("P01", highlight: ("T001", "S001"), frame: "highlight", zoom: 1.5), kind: image, caption: [P01]) <fig-p01>'
    assert pcb.command_text({"plan": "P01", "caption": False}) == '#figure(image-positions-plan("P01"), kind: image) <fig-p01>'
    assert pcb.command_text({"plan": "P01", "caption": "Plan Nord"}) == '#figure(image-positions-plan("P01"), kind: image, caption: [Plan Nord]) <fig-p01>'
    assert pcb.command_text({"plan": "P01", "caption": None, "width": "100%"}) == '#figure(image-positions-plan("P01"), kind: image, caption: [P01]) <fig-p01>'


def test_a_detail_needs_a_highlighted_position_and_a_zoom_a_detail_and_a_width_that_is_none_is_left_out():
    _qt()
    import plan_command_builder as pcb
    # asked for, but nothing highlighted: no detail, and so no zoom either -- the call says nothing a reader could believe
    assert pcb.command_text({"plan": "P01", "detail": True, "zoom": 2}) == '#figure(image-positions-plan("P01"), kind: image, caption: [P01]) <fig-p01>'
    assert pcb.command_text({"plan": "P01", "highlight": ["T001"], "detail": False, "zoom": 2}) == '#figure(image-positions-plan("P01", highlight: "T001"), kind: image, caption: [P01]) <fig-p01>'
    for bad in ("", "wide", "60", "60 %", "%"):
        assert pcb.valid_width(bad) is None, bad
    assert pcb.valid_width("12cm") == "12cm" and pcb.valid_width(" 60% ") == "60%" and pcb.valid_width("100%") is None


def test_the_controls_say_the_command_and_what_has_no_effect_is_greyed():
    pcb, options = _options()
    values = options.values()
    assert values["plan"] == "P01" and values["highlight"] == [] and values["detail"] is False and values["caption"] is None
    assert pcb.command_text(values) == '#figure(image-positions-plan("P01"), kind: image, caption: [P01]) <fig-p01>'
    # a plan with a scale: its bar is offered; nothing highlighted: no detail, no zoom
    assert options.scale_bar.isEnabled() and not options.detail.isEnabled() and not options.zoom.isEnabled()
    _tick(options, "S001", "T001")
    assert options.detail.isEnabled() and not options.zoom.isEnabled()
    options.detail.setChecked(True)
    assert options.zoom.isEnabled()
    options.zoom.setValue(2)
    assert pcb.command_text(options.values()) == '#figure(image-positions-plan("P01", highlight: ("T001", "S001"), frame: "highlight", zoom: 2), kind: image, caption: [P01]) <fig-p01>'
    # the highlighted positions are read in the order the plan lists them
    assert options.values()["highlight"] == ["T001", "S001"]
    # unticking the last position takes the detail with it, and the call
    _tick(options)
    assert not options.detail.isEnabled() and options.values()["detail"] is False
    assert pcb.command_text(options.values()) == '#figure(image-positions-plan("P01"), kind: image, caption: [P01]) <fig-p01>'
    # a plan without a scale has no bar to draw: the option is greyed, says why, and writes nothing whatever it holds
    options.plan.setCurrentIndex(options.plan.findData("P02"))
    assert not options.scale_bar.isEnabled() and options.scale_bar.toolTip()
    options.scale_bar.setChecked(False)
    assert options.values()["scale_bar"] is True and "scale-bar" not in pcb.command_text(options.values())
    # the caption
    assert not options.caption_text.isEnabled()
    options.caption.setCurrentIndex(options.caption.findData("none"))
    assert pcb.command_text(options.values()) == '#figure(image-positions-plan("P02"), kind: image) <fig-p02>'
    options.caption.setCurrentIndex(options.caption.findData("custom"))
    assert options.caption_text.isEnabled()
    options.caption_text.setText("Hauptgebäude")
    assert pcb.command_text(options.values()) == '#figure(image-positions-plan("P02"), kind: image, caption: [Hauptgebäude]) <fig-p02>'


def test_a_plan_chosen_brings_its_own_positions_and_clears_the_highlight_of_the_other():
    pcb, options = _options()
    _tick(options, "S001")
    options.plan.setCurrentIndex(options.plan.findData("P02"))
    assert [options.positions.item(i).text() for i in range(options.positions.count())] == ["T003"]
    assert options.values()["highlight"] == [] and options.values()["detail"] is False
    options.set_plan("P01")
    assert options.current_plan() == "P01" and options.positions.count() == 3
    options.set_plans([{"id": "Q", "labels": ["A001"]}])    # a list of records is read as the export's dictionary is
    assert options.current_plan() == "Q" and options.positions.count() == 1


def test_changed_is_emitted_for_the_engineers_edits_and_not_for_what_the_tab_says():
    pcb, options = _options()
    seen = []
    options.changed.connect(seen.append)
    options.set_plans(PLANS)
    options.set_plan("P02")
    assert seen == [], "the tab saying which plan is open is not an edit"
    options.legend.setChecked(False)
    assert len(seen) == 1 and seen[-1]["legend"] is False
    options.width.setCurrentText("60%")
    assert seen[-1]["width"] == "60%"
    options.plan.setCurrentIndex(options.plan.findData("P01"))
    assert seen[-1]["plan"] == "P01"
    _tick(options, "T001")
    assert seen[-1]["highlight"] == ["T001"]
    options.caption.setCurrentIndex(options.caption.findData("none"))
    assert seen[-1]["caption"] is False
    before = len(seen)
    options.width.setCurrentText("not a width")
    assert len(seen) == before + 1 and seen[-1]["width"] is None, "a width Typst would not read is left out of the call"


def test_the_words_are_in_three_languages_with_the_same_keys_and_no_hex_colour():
    _qt()
    import plan_command_builder as pcb
    keys = {lang: set(table) for lang, table in pcb.STRINGS.items()}
    assert set(keys) == {"fr", "de", "en"} and keys["fr"] == keys["de"] == keys["en"]
    assert all(key.startswith("pcb_") for key in keys["en"])
    assert not any("ß" in word for word in pcb.STRINGS["de"].values()), "Swiss German is never written with an ß"
    source = (TOOLS / "plan_command_builder.py").read_text(encoding="utf-8")
    assert "setStyleSheet" not in source
    for lang in ("fr", "de"):
        options = pcb.CommandOptions(lang)
        assert options.display_card.title() == pcb.text("pcb_display_card", lang)
        assert options.display_card.title() != pcb.text("pcb_display_card", "en")
    options.set_language("en")
    assert options.legend.text() == pcb.text("pcb_legend", "en")


def _builder(name):
    app = _qt()
    import plan_command_builder as pcb
    copied = []
    builder = pcb.CommandBuilder("en", copy=copied.append)
    builder.pane.preview_folder = conftest.tmpdir(name + "-cache")
    return app, pcb, builder, copied


def test_the_builder_shows_the_command_copies_it_and_asks_for_a_page_of_it():
    app, pcb, builder, copied = _builder("pcb_builder")
    try:
        assert not builder.copy_button.isEnabled() and builder.field.text() == "" and builder.source() is None
        builder.set_plans(PLANS)
        assert builder.field.text() == '#figure(image-positions-plan("P01"), kind: image, caption: [P01]) <fig-p01>' and builder.copy_button.isEnabled()
        builder.options.legend.setChecked(False)
        assert builder.field.text() == '#figure(image-positions-plan("P01", detail-legend: "scale-bar"), kind: image, caption: [P01]) <fig-p01>' and builder.command() == builder.field.text()
        builder.copy_button.click()
        assert copied == ['#figure(image-positions-plan("P01", detail-legend: "scale-bar"), kind: image, caption: [P01]) <fig-p01>']
        # without a project nothing is asked of Typst, and the pane says why
        assert builder.source() is None and not builder.pane.is_pending()
        assert builder.pane.placeholder.text() == pcb.text("pcb_no_project", "en")
        builder.set_language("fr")
        assert builder.heading.text() == pcb.text("pcb_command", "fr") and builder.field.text() == '#figure(image-positions-plan("P01", detail-legend: "scale-bar"), kind: image, caption: [P01]) <fig-p01>'
    finally:
        builder.stop()
        builder.deleteLater()


def test_the_snippet_is_the_header_and_the_call_and_it_compiles_to_the_plan():
    """The preview's real work: the source the pane compiles from standard input against the project's folder, shown as a page -- the project made by `project_template.create`, given the example project's export (plans.json and what it names)."""
    if not conftest.have_typst():
        raise Skip("typst is not installed here")
    import json
    import project
    import project_template
    import structure_preview
    app, pcb, builder, copied = _builder("pcb_compile")
    try:
        example = project.current()
        base = conftest.tmpdir("pcb_project")
        here = project_template.create(base / "Halle", "Halle", document_language="en", report_language="en", author="L. Exempel")
        shutil.copytree(example.data_dir, here.data_dir, dirs_exist_ok=True)
        for kind in project.FIGURE_KINDS:   # and the figures it names, in the tabs' Exports/ laid out by folders (issue #64)
            if example.has_folders and example.exports_dir(kind).is_dir():
                shutil.copytree(example.exports_dir(kind), here.exports_dir(kind), dirs_exist_ok=True)
        records = json.loads((here.data_dir / "plans.json").read_text(encoding="utf-8"))["plans"]
        assert "Pavillon" in records

        pdfs = set(here.root.rglob("*.pdf"))
        builder.set_project(here)
        builder.set_plans(records)
        builder.set_plan("Pavillon")
        builder.options.legend.setChecked(False)
        _tick(builder.options, "T001")
        mode = builder.mode
        assert mode in here.modes
        values = builder.options.values()
        source = pcb.snippet_source(here, mode, values, "en")
        assert source == builder.source() and source.splitlines()[:3] == structure_preview.header(here, mode, "en")[:3]
        assert source.rstrip().endswith('#figure(image-positions-plan("Pavillon", detail-legend: "scale-bar", highlight: "T001"), kind: image, caption: [Pavillon]) <fig-pavillon>'), source
        assert source.count("image-positions-plan(") == 1

        # the pane compiles it, shows it, and says the command it shows
        end = time.monotonic() + 90
        while builder.pane.shown_snippet != builder.command():
            assert time.monotonic() < end, f"no page after 90 s: {builder.pane.last_error}"
            app.processEvents()
            time.sleep(0.02)
        assert builder.pane.error_banner.isHidden(), builder.pane.last_error
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(open(builder.pane.shown, "rb").read()))
        words = " ".join(page.extract_text() or "" for page in reader.pages)
        assert reader.pages and "Pavillon" in words, words[:300]
        assert set(here.root.rglob("*.pdf")) == pdfs, "a preview is never written into the project"

        # a change of option asks for another page, and a call Typst refuses leaves the banner and the last page
        builder.options.caption.setCurrentIndex(builder.options.caption.findData("none"))
        end = time.monotonic() + 90
        while builder.pane.shown_snippet != builder.command():
            assert time.monotonic() < end, "no second page"
            app.processEvents()
            time.sleep(0.02)
        assert 'caption:' not in builder.command(), "«no caption»: the figure is written without one"
    finally:
        builder.stop()
        builder.deleteLater()


def test_the_builder_takes_the_controls_and_the_command_of_another_kind_of_plan():
    app = _qt()
    import plan_command_builder as pcb
    made = []

    class FakeOptions(pcb.CommandOptions):
        def __init__(self, lang):
            made.append(lang)
            super().__init__(lang)

    builder = pcb.CommandBuilder("en", copy=lambda text: None, options_factory=FakeOptions, command_fn=lambda values: f"#show-fire-plan({values.get('plan')!r})")
    builder.pane.preview_folder = conftest.tmpdir("pcb_factory-cache")
    try:
        assert made == ["en"] and isinstance(builder.options, FakeOptions)
        builder.set_plans(PLANS)
        assert builder.command() == "#show-fire-plan('P01')" and builder.field.text() == builder.command()
        # the default builder is the position plan's: its figure (spec 2026-10-21-commandes-typst-refonte, REQ-013)
        default = pcb.CommandBuilder("en", copy=lambda text: None)
        default.pane.preview_folder = conftest.tmpdir("pcb_default-cache")
        try:
            default.set_plans(PLANS)
            assert default.command() == '#figure(image-positions-plan("P01"), kind: image, caption: [P01]) <fig-p01>' and type(default.options) is pcb.CommandOptions
        finally:
            default.stop()
            default.deleteLater()
    finally:
        builder.stop()
        builder.deleteLater()


# --- the fire-protection plan's builder (v0.115) ------------------------------------------------------------

FIRE_PLANS = {
    "Treppenhaus": {"label": "Regelgeschoss", "scale": {"mode": "calibration", "units_per_m": 20}},
    "Pavillon-EG": {"label": "Erdgeschoss"},
}


def test_the_fire_command_is_show_fire_plan_with_only_what_differs_from_its_defaults():
    _qt()
    import plan_command_builder as pcb
    # a native figure since the spec 2026-10-21-commandes-typst-refonte (REQ-014, ARCH-012)
    assert pcb.fire_command_text({"plan": "Treppenhaus"}) == '#figure(image-fire-plan("Treppenhaus"), kind: image, caption: [Treppenhaus]) <fig-treppenhaus>'
    assert pcb.fire_command_text({"plan": "Treppenhaus", "width": "60%", "legend": False, "scale_bar": False}) == \
        '#figure(image-fire-plan("Treppenhaus", detail-legend: "none", width: 60%), kind: image, caption: [Treppenhaus]) <fig-treppenhaus>'
    assert pcb.fire_command_text({"plan": "Treppenhaus", "caption": False}) == '#figure(image-fire-plan("Treppenhaus"), kind: image) <fig-treppenhaus>'
    assert pcb.fire_command_text({"plan": "Treppenhaus", "caption": "Plan Nord"}) == '#figure(image-fire-plan("Treppenhaus"), kind: image, caption: [Plan Nord]) <fig-treppenhaus>'
    assert pcb.fire_command_text({"plan": "Treppenhaus", "caption": None, "width": "100%"}) == '#figure(image-fire-plan("Treppenhaus"), kind: image, caption: [Treppenhaus]) <fig-treppenhaus>'
    # a position plan's detail, axes and highlight mean nothing to a fire plan: they are not written
    assert pcb.fire_command_text({"plan": "Treppenhaus", "axes": False, "highlight": ["T001"], "detail": True}) == '#figure(image-fire-plan("Treppenhaus"), kind: image, caption: [Treppenhaus]) <fig-treppenhaus>'


def test_the_fire_controls_are_the_plans_less_the_axes_the_positions_and_the_detail():
    _qt()
    import plan_command_builder as pcb
    options = pcb.FireCommandOptions("fr")
    options.set_plans(FIRE_PLANS)
    assert options.current_plan() == "Treppenhaus"
    assert options.axes.isHidden() and options.highlight_card.isHidden() and not options.display_card.isHidden()
    assert options.legend.text() == pcb.text("pcb_fire_legend", "fr") and options.legend.text() != pcb.text("pcb_legend", "fr")
    assert set(options.values()) == {"plan", "width", "legend", "scale_bar", "caption", "level"}   # the level since v0.120 (UI-003)
    got = []
    options.changed.connect(got.append)
    options.legend.setChecked(False)
    options.width.setCurrentText("60%")
    assert got[-1] == {"plan": "Treppenhaus", "width": "60%", "legend": False, "scale_bar": True, "caption": None, "level": None}
    # the scale bar follows the plan's scale: greyed where the plan has none
    assert options.scale_bar.isEnabled()
    options.plan.setCurrentIndex(options.plan.findData("Pavillon-EG"))
    assert not options.scale_bar.isEnabled() and options.values()["plan"] == "Pavillon-EG"
    options.set_language("de")
    assert options.legend.text() == pcb.text("pcb_fire_legend", "de")
    for lang in ("fr", "de", "en"):
        assert "pcb_fire_legend" in pcb.STRINGS[lang]


def test_the_snippet_takes_the_builders_own_command_and_a_fire_plan_compiles_through_it():
    """`snippet_source(command_fn=…)` was written to take another kind of plan's command and ignored it until v0.115: the preview of a fire plan compiled `#show-plan`."""
    if not conftest.have_typst():
        raise Skip("typst is not installed here")
    import json
    import project
    import project_template
    app = _qt()
    import plan_command_builder as pcb
    here = project_template.create(conftest.tmpdir("pcb_fire_project") / "Halle", "Halle", document_language="en", report_language="en", author="L. Exempel")
    shutil.copytree(project.current().data_dir, here.data_dir, dirs_exist_ok=True)
    for kind in project.FIGURE_KINDS:   # and the figures it names, in the tabs' Exports/ laid out by folders (issue #64)
        if project.current().has_folders and project.current().exports_dir(kind).is_dir():
            shutil.copytree(project.current().exports_dir(kind), here.exports_dir(kind), dirs_exist_ok=True)
    records = json.loads((here.data_dir / "fire.json").read_text(encoding="utf-8"))["plans"]
    builder = pcb.CommandBuilder("en", copy=lambda text: None, options_factory=pcb.FireCommandOptions, command_fn=pcb.fire_command_text)
    builder.pane.preview_folder = conftest.tmpdir("pcb_fire-cache")
    try:
        builder.set_project(here)
        builder.set_plans(records)
        builder.set_plan("Treppenhaus")
        builder.options.legend.setChecked(False)
        source = builder.source()
        assert source.rstrip().endswith('#figure(image-fire-plan("Treppenhaus", detail-legend: "scale-bar"), kind: image, caption: [Treppenhaus]) <fig-treppenhaus>') and "image-positions-plan(" not in source, source
        assert pcb.snippet_source(here, builder.mode, builder.options.values(), None, pcb.fire_command_text) == source
        end = time.monotonic() + 90
        while builder.pane.shown_snippet != builder.command():
            assert time.monotonic() < end, f"no page after 90 s: {builder.pane.last_error}"
            app.processEvents()
            time.sleep(0.02)
        assert builder.pane.error_banner.isHidden(), builder.pane.last_error
        from pypdf import PdfReader
        words = " ".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(open(builder.pane.shown, "rb").read())).pages)
        assert "Treppenhaus" in words, words[:300]   # the figure's caption, the plan's id until the engineer writes his own
    finally:
        builder.stop()
        builder.deleteLater()
