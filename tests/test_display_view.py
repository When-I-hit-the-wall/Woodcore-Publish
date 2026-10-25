"""The «Affichage» views (v0.117, calc/tools/display_view.py and display_options.py; spec docs/requirements/active/2026-10-07-vues-onglets-slider-et-volets.md, REQ-007 to REQ-009, ARCH-002, ARCH-005 to ARCH-007).

The engineer, 07.10.2026: «dans le mode affichage … au centre, on a le compilé comme cela apparaîtrait dans le rapport. Et dans le volet de droite, on a les différentes options pour la commande, ainsi qu'on peut copier à la fin la commande» -- and, answering Q-001, every command's panel written by hand now. What is held here: that every panel offers each named argument of its command or says why not (a command that gains an argument in lib/ fails here until its panel is told), that a control starts at the default the signature writes and never at one of its own, that a call made with each option changed compiles, that the words exist in three languages, and that the shared widget compiles nothing it does not show.
"""

TIER = "fast"  # tests/run_tests.py --fast

import os
import subprocess
import sys
from pathlib import Path

import conftest
from conftest import ROOT, Skip

sys.path.insert(0, str(ROOT / "calc" / "tools"))

import build_reference as ref  # noqa: E402
import display_options as opts  # noqa: E402
import project  # noqa: E402


def _qt():
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError as exc:
        raise Skip(f"PySide6 is not installed ({exc})")
    return QApplication.instance() or QApplication([])


def _t(key, **values):
    text = opts.STRINGS["en"][key]
    return text.format(**values) if values else text


def test_every_named_argument_is_offered_or_dismissed_with_its_reason():
    gaps = []
    for name, spec in opts.SPECS.items():
        defaults = ref.signature_defaults(name)
        offered = {option.name for option in spec.options} | {more for option in spec.options for more in option.also}   # a `columns` control writes its widths too
        dismissed = opts.DISMISSED.get(name, {})
        for option in offered:
            assert option in defaults, f"{name}: the panel offers {option!r}, which the command does not take"
        for argument, default in defaults.items():
            if default is None or argument.startswith(ref.VARIADIC):
                continue      # a positional argument: the tab hands it over (Spec.positional)
            if argument not in offered and not dismissed.get(argument):
                gaps.append(f"{name}: {argument}")
        for argument in dismissed:
            assert argument in defaults and argument not in offered, f"{name}: {argument!r} is dismissed and offered, or is no argument"
    assert not gaps, "named arguments no panel offers and none dismisses with a reason:\n  " + "\n  ".join(gaps)


def test_a_panel_writes_no_default_of_its_own_and_starts_at_the_signatures():
    """A declaration holds no default (display_options' docstring); the controls start at the signature's, so a call made from an untouched panel is the bare call."""
    _qt()
    import display_view
    for name, spec in opts.SPECS.items():
        assert not any(hasattr(option, "default") for option in spec.options), name
        panel = display_view.SpecPanel(spec, _t)
        positional = ["X"] * len(spec.positional)
        assert ref.call_command(name, *positional, **panel.values()) == ref.call_command(name, *positional), (name, panel.values())


def test_the_words_are_in_three_languages_and_every_key_a_panel_names_exists():
    reference = set(opts.STRINGS["fr"])
    for lang in ("de", "en"):
        assert set(opts.STRINGS[lang]) == reference, (lang, sorted(set(opts.STRINGS[lang]) ^ reference))
    for spec in opts.SPECS.values():
        for option in spec.options:
            assert option.label in reference, option.label
            if option.kind == "choice":
                for value in option.choices:
                    assert f"ds_choice_{value}" in reference, value
        for title, _names in spec.cards:
            assert title in reference, title
    for key in opts.NOTES.values():
        assert key in reference, key


# What each kind of option is set to, away from its default, for a call that must still compile.
CHANGED = {"bool": None, "width": ref.Raw("60%"), "level": 2, "title": "Titre", "caption": "Légende", "number": 1.5, "switch": False}   # a switch left at its auto, changed: off (UI-003)
TEXTS = {"storey": "0", "unit": "kN/m^2", "label": "Libellé", "descr": "Pourquoi", "norm": "SIA 265", "norm-ref": "2.2.5"}
# An option changed together with the one it makes count: a list of the positions of one storey names the storey.
TOGETHER = {}


def _changed(option, default):
    if option.kind == "bool":
        return default.strip() != "true"
    if option.kind == "choice":
        others = [c for c in option.choices if c and f'"{c}"' != default]
        return others[0] if others else None
    if option.kind == "text":
        return TEXTS.get(option.name)
    if option.kind == "ids":
        return None
    if option.kind == "columns":
        return ("id", "type", "description")
    return CHANGED[option.kind]


def test_a_call_with_each_option_changed_compiles():
    """Every option of every panel, changed alone, in a call that compiles against the example's export -- the commands that name a variable a report declares first (val, var, find) are left to tests/test_commands.py, as there, and so is show-check, which the example gives nothing to name."""
    if not conftest.have_typst():
        raise Skip("typst is not on PATH")
    samples = {key: value.strip('"') if value.startswith('"') else ref.Raw(value) for key, value in ref.sample_arguments(project.current().data_dir).items()}
    samples["id"] = samples.get("check")
    probe = conftest.probe_dir("display_calls")
    failures = []
    for name, spec in opts.SPECS.items():
        if name in ("val", "var", "find", "show-check", "eq", "verify", "var-unit"):
            continue      # eq, verify and var-unit name variables a domain declares first: compiled in tests/test_formula_domain.py and tests/test_units.py
        positional = [samples[p] for p in spec.positional]
        defaults = ref.signature_defaults(name)
        calls = [ref.call_command(name, *positional)]
        for option in spec.options:
            if option.needs:
                continue      # an option that has an effect only with another, or with what the object carries: changed with it below, or greyed
            value = _changed(option, defaults[option.name])
            if value is not None:
                calls.append(ref.call_command(name, *positional, **{option.name: value, **TOGETHER.get((name, option.name), {})}))
        doc = probe / f"{name}.typ"
        doc.write_text('#import "/000-Typst-Config/commands.typ": *\n' + "\n\n".join(calls) + "\n", encoding="utf-8")
        r = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(doc), str(doc.with_suffix(".pdf"))],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        if r.returncode != 0:
            failures.append(f"{name}: {r.stderr.strip()[:400]}")
    assert not failures, "calls of the panels that do not compile:\n  " + "\n  ".join(failures)


def test_every_level_a_panel_offers_compiles():
    """ARCH-008 (issue #20): a panel offers a command the levels it accepts and no other -- 0 was offered to show-calc, show-input, show-live-load, show-connector-resistance and show-polar-moment, which refuse it, and their preview failed --, and never -1, the «Sélection manuelle» the engine no longer has (spec 2026-10-22-retrait-niveau-manuel, REQ-001)."""
    if not conftest.have_typst():
        raise Skip("typst is not on PATH")
    _qt()
    import display_view
    samples = {key: value.strip('"') if value.startswith('"') else ref.Raw(value) for key, value in ref.sample_arguments(project.current().data_dir).items()}
    probe = conftest.probe_dir("display_levels")
    failures = []
    for name, spec in opts.SPECS.items():
        if name in ("val", "var", "find", "show-check", "eq", "verify", "var-unit"):
            continue
        panel = display_view.SpecPanel(spec, lambda key, **kw: opts.STRINGS["en"].get(key, key))
        for option_name, (option, control) in panel.controls.items():
            if option.kind != "level":
                continue
            offered = [control.itemData(i) for i in range(control.count())]
            assert "-1" not in offered, (name, offered)
            calls = []
            for value in offered:
                if value in ("auto", "none"):
                    continue
                calls.append(ref.call_command(name, *[samples[p] for p in spec.positional], **{option_name: int(value)}))
            doc = probe / f"{name}.typ"
            doc.write_text('#import "/000-Typst-Config/commands.typ": *\n' + "\n\n".join(calls) + "\n", encoding="utf-8")
            r = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(doc), str(doc.with_suffix(".pdf"))],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
            if r.returncode != 0:
                failures.append(f"{name} {offered}: {r.stderr.strip()[:300]}")
        panel.deleteLater()
    assert not failures, "levels offered that do not compile:\n  " + "\n  ".join(failures)


def test_the_manual_selection_is_gone_from_the_window():
    """Spec 2026-10-22-retrait-niveau-manuel, REQ-001 to REQ-005 (issue #93): the level of detail -1 «Sélection manuelle» left the engine with the Typst overhaul, and the window keeps nothing of it -- no kind of control that offers it, no -1 in any panel's levels, no word of it in any language, no module that reads what it could name (calc/shown_variables.py, lib/shown-variables.json), and no file of calc/ that imports it."""
    import re
    assert "detail" not in opts.KINDS and not hasattr(opts, "SELECTION") and not hasattr(opts, "LEVELS_SHOWN")
    assert all(o.kind in opts.KINDS for spec in opts.SPECS.values() for o in spec.options)
    assert all("-1" not in (o.choices or ()) for spec in opts.SPECS.values() for o in spec.options if o.kind == "level")
    for lang, words in opts.STRINGS.items():
        assert not [k for k in words if k == "ds_level_manual" or re.match(r"ds_shown(_|$)", k)], lang
    assert not (ROOT / "calc" / "shown_variables.py").exists() and not (ROOT / "lib" / "shown-variables.json").exists()
    readers = [str(p.relative_to(ROOT)) for p in (ROOT / "calc").rglob("*.py") if re.search(r"\bshown_variables\b|shown-variables\.json|\bLevelControl\b", p.read_text(encoding="utf-8"))]
    assert not readers, readers


def test_a_command_the_formules_tab_writes_has_one_declaration_and_two_views():
    """Issue #19 (ARCH-RISK-W01): «Calcul» offers what a line is -- label, description, norm, clause --, «Affichage» how it is printed -- level, display type, style, summary --; the two views of var together are the whole declaration and share no option. Since issue #113 the clause is `norm-section:` (REQ-008), and `eq` and `verify`, which only the retired panel of the «Domaines» tab read, have no declaration (calc/domains/formula_args.py offers their arguments)."""
    spec = opts.spec("var")
    calc = {o.name for o in spec.for_view("calc").options}
    display = {o.name for o in spec.for_view("display").options}
    assert calc | display == {o.name for o in spec.options} and not calc & display
    assert calc == {"label", "descr", "norm", "norm-section"}, calc
    assert {"level", "style"} <= display, display
    assert "eq" not in opts.SPECS and "verify" not in opts.SPECS


def test_the_view_compiles_nothing_it_does_not_show_and_each_tab_has_its_own_folder():
    _qt()
    import display_view
    first = display_view.DisplayView(_t, cache_key="tab_a")
    second = display_view.DisplayView(_t, cache_key="tab_b")
    asked = []
    first.set_entries([display_view.Entry("m", "image-static-model", "image-static-model", positional=("Bankli-Fall1",))])
    assert first._pane is None, "the pane is made the first time the view is shown, not before"
    first.set_project(project.current(), None)
    assert first._pane is None, "a project set is no reason to compile"
    first.pane.request_snippet = lambda *a: asked.append(a)
    first.refresh()
    assert not asked, "nothing is compiled while the view is not shown"
    first.activate(True)
    assert len(asked) == 1 and asked[0][2].rstrip().endswith('#image-static-model("Bankli-Fall1")'), asked
    assert first.pane.preview_folder != second.pane.preview_folder, "two tabs compiling at once never write one file"
    first.activate(False)


def test_a_command_chosen_changes_the_call_and_the_options_and_a_note_replaces_the_page():
    _qt()
    import display_view
    view = display_view.DisplayView(_t, cache_key="tab_c")
    view.set_project(project.current(), None)
    entries = [
        display_view.Entry("var", "var", "var", call_fn=lambda o: ref.call_var_domain("snow-load", "SL", "s_k", **o)),
        display_view.Entry("model", "image-static-model", "image-static-model", positional=("Bankli-Fall1",)),
        display_view.Entry("entries", "journal-entries", "journal-entries", call_fn=lambda o: ref.call_journal_entries(o.get("document")), note="ds_note_prints_nothing"),
    ]
    view.set_entries(entries)
    assert view.command() == '#var("s_k", domain: ("snow-load", "SL"))'
    var_panel = view.panel()
    _option, style = var_panel.controls["style"]
    style.setCurrentIndex(style.findData("bold"))
    assert view.command() == '#var("s_k", domain: ("snow-load", "SL"), style: "bold")' and view.field.text() == view.command()
    view.chooser.setCurrentIndex(1)
    assert view.command() == '#image-static-model("Bankli-Fall1")' and view.panel() is not var_panel, "another command, its own options"
    view.chooser.setCurrentIndex(2)
    view.activate(True)
    assert not view.note.isHidden() and view.note.text() == _t("ds_note_prints_nothing")
    assert view._pane is None or not view._pane.isVisible(), "a command that prints nothing is not compiled"
    view.set_entries(entries[:2])
    assert view.current().key == "var", "the command chosen is kept where it is still offered, else the first"


def test_the_panels_of_their_own_write_the_drawings_figure():
    """ARCH-006, ARCH-012 for the two panels that are widgets of their own (display_options.OWN_PANELS): each switch of what the plan shows a word of the image's vocabulary, and an untouched panel the bare figure -- the drawing's native figure since the spec 2026-10-21-commandes-typst-refonte (REQ-013, REQ-014)."""
    _qt()
    import plan_command_builder as pcb
    assert set(opts.OWN_PANELS) == {"image-positions-plan", "image-fire-plan"}
    vocabulary = ref.image_vocabulary()
    for image, factory, call in (("image-positions-plan", pcb.CommandOptions, pcb.command_text), ("image-fire-plan", pcb.FireCommandOptions, pcb.fire_command_text)):
        options = factory("en")
        options.set_plans([{"id": "P01", "labels": ["A1"], "scale": 100}])
        assert call(options.values()) == f'#figure({image}("P01"), kind: image, caption: [P01]) <fig-p01>', (image, call(options.values()))
        assert image in vocabulary, image


def test_var_and_find_with_each_option_changed_compile_on_a_value_of_the_export():
    """The two commands of the variables tab, on a value of the example's export (`q_k1` of the snow case SL, a flat roof) and its domain: each option changed alone, in a call that compiles."""
    if not conftest.have_typst():
        raise Skip("typst is not on PATH")
    probe = conftest.probe_dir("display_variable_calls")
    texts = dict(TEXTS, unit="N/m^2")
    calls = []
    for command, make in (("var", lambda o: ref.call_var_domain("snow-load", "SL", "q_k1", **o)),):
        defaults = ref.signature_defaults(command)
        calls.append(make({}))
        for option in opts.spec(command).options:
            if option.kind == "text":
                value = texts.get(option.name)
            else:
                value = _changed(option, defaults[option.name])
            if value is not None:
                calls.append(make({option.name: value}))
    defaults = ref.signature_defaults("find")
    for option in opts.spec("find").options:
        calls.append(ref.call_command("find", object="variable", domain=("snow-load", "SL"), **{option.name: _changed(option, defaults[option.name])}))
    doc = probe / "variables.typ"
    doc.write_text('#import "/000-Typst-Config/commands.typ": *\n' + "\n\n".join(calls) + "\n", encoding="utf-8")
    r = subprocess.run(["typst", "compile", "--root", str(conftest.TYPST_ROOT), str(doc), str(doc.with_suffix(".pdf"))],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    assert r.returncode == 0, "calls of var and find that do not compile:\n" + r.stderr.strip()[:800] + "\n" + "\n".join(calls)


def test_the_banner_says_what_the_export_lacks_beside_the_import_button():
    """Review B04: an object not in the export, or changed since it, is said above the page with «Import données» beside it -- the engineer's click, never an export in silence; an object up to date shows neither."""
    _qt()
    import display_view
    imported = []
    view = display_view.DisplayView(_t, cache_key="tab_banner", import_fn=lambda: imported.append(True), import_text="Import data")
    view.set_project(project.current(), None)
    banner = display_view.export_state(_t, "S9", exported=False)
    assert banner == _t("ds_not_exported", id="S9")
    view.set_entries([display_view.Entry("m", "image-static-model", "image-static-model", positional=("S9",), banner=banner)])
    assert not view.banner.isHidden() and view.banner.text() == banner and not view.import_button.isHidden()
    view.import_button.click()
    assert imported == [True], "the button imports nothing"
    view.set_entries([display_view.Entry("m", "image-static-model", "image-static-model", positional=("Bankli-Fall1",))])
    assert view.banner.isHidden() and view.import_button.isHidden()
    # a source written after the export is «changed since the last export»
    import os
    import tempfile
    import time
    folder = Path(tempfile.mkdtemp(dir=conftest.probe_dir("display_banner")))
    export, source = folder / "statics.json", folder / "S1.json"
    export.write_text('{"models": {"S1": {}}}', encoding="utf-8")
    source.write_text("{}", encoding="utf-8")
    later = time.time() + 60
    os.utime(source, (later, later))
    assert display_view.saved_state(_t, "S1", "unsaved", False, export, "models", source) == _t("ds_stale", id="S1")
    assert display_view.saved_state(_t, "S1", "unsaved", True, export, "models", source) == "unsaved"
    os.utime(source, (time.time() - 3600, time.time() - 3600))
    assert display_view.saved_state(_t, "S1", "unsaved", False, export, "models", source) == ""


def test_the_options_chosen_survive_the_rebuild_of_the_window_in_memory():
    """v0.117 (D-012): every export ends in a rebuild of the tabs, which gave every «Affichage» panel its defaults back; the window keeps the state of each and gives it to the tabs it builds."""
    _qt()
    import display_view
    entry = lambda: display_view.Entry("model", "image-static-model", "image-static-model", positional=("Bankli-Fall1",),   # noqa: E731
                                       context={"highlight": ["M1", "M2"], "detail-figure": ["loads", "dimensions"]})
    first = display_view.DisplayView(_t, copy=lambda text: None, import_line=False)
    first.set_entries([entry()])
    first.panel().set_values({"highlight": ["M2"], "detail-figure": ["dimensions"], "width": "60%"})
    before = first.values()
    assert before["highlight"] == "M2" and before["detail-figure"] == "dimensions", before
    snapshot = first.snapshot()
    second = display_view.DisplayView(_t, copy=lambda text: None, import_line=False)   # the window after the rebuild: nothing chosen yet
    second.restore(snapshot)
    second.set_entries([entry()])
    assert second.values() == before, (second.values(), before)
    assert second.command() == first.command()
    # an object the snapshot knows nothing of still starts at the defaults
    third = display_view.DisplayView(_t, copy=lambda text: None, import_line=False)
    third.restore({})
    third.set_entries([entry()])
    assert third.command() == '#image-static-model("Bankli-Fall1")', third.command()

