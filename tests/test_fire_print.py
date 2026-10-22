"""What the report and an export sheet print of a fire-protection plan (v0.115): `#image-fire-plan` -- `#show-fire-plan` until the spec 2026-10-21-commandes-typst-refonte (REQ-014) --, `#ids("fire-plan")`, and the objects of an export sheet, a fire plan and its legend (lib/calc-engine.typ, lib/document.typ, lib/sheet.typ).

What is held:

* a fire plan prints **in the report's language** -- its legend, drawn once per language by calc/domains/fire_svg.py, carries words -- with its figure number, its scale bar where it has a scale and its legend where `detail-legend` names it;
* `detail-legend` without `objects` takes the legend **off the plan** and nothing else;
* `ids("fire-plan")` lists the plans of data/fire.json, an unknown id is refused listing them;
* on a sheet **the legend is both possible**: drawn on the plan (`legend: true`) and as an object of its own (`sheet-fire-legend`), once each, so a sheet may carry it twice, once or not at all; the scale a fire plan is printed at is the one the title block names; a plan with no scale cannot be given one, and the refusal says the fire-protection plan tab;
* the fire legend's lines carry their own wording (`term` or `engine`), which `plan-legend` translates -- the position plan's STE lines still go by their key.

⚠️ Every compiled check is skipped where `typst` is not on the path. Each works on a copy of the example project of its own, its engine synced -- the position plans' pages are not compared here: the generalised `plan-figure` was checked byte for byte against the engine before it, on `show-plan` of every plan of the example project, in the change that made it.
"""

import json
import re
import shutil
import subprocess
import unicodedata

import conftest
from conftest import ROOT, Skip
import project
import sheets
import typst_objects as to

SAMPLE = ROOT / "tests" / "projet-exemple"


def _need_typst():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


def _project(name):
    """A copy of the example project, its engine synced."""
    root = conftest.tmpdir(name) / "Exemple"
    shutil.copytree(SAMPLE, root, ignore=shutil.ignore_patterns("lib", "VERSION", "stamps", "_Archiv"))
    here = project.Project.load(root / "Exemple.woodcore")
    project.sync_engine(here)
    return here


def _text_of(pdf):
    from pypdf import PdfReader
    return unicodedata.normalize("NFKC", "\n".join(p.extract_text() for p in PdfReader(str(pdf)).pages))


def _run(here, body, name, lang="de"):
    """The probe's code and stderr, and where its PDF is."""
    _need_typst()
    d = here.typst_root / ".probe" / name
    d.mkdir(parents=True, exist_ok=True)
    probe = d / "probe.typ"
    probe.write_text('#import "/000-Typst-Config/config.typ": conf\n#import "/000-Typst-Config/commands.typ": *\n#report-level.update(2)\n#show: conf\n'
                     f'#set-report-language("{lang}")\n' + body + "\n", encoding="utf-8")
    out = d / "probe.pdf"
    run = subprocess.run([project.typst_executable(), "compile", "--root", str(here.typst_root), str(probe), str(out)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return run.returncode, run.stderr, out


def _text(here, body, name, lang="de"):
    code, err, out = _run(here, body, name, lang)
    assert code == 0, err
    return _text_of(out)


def _refusal(here, body, name):
    code, err, _ = _run(here, body, name)
    assert code != 0, f"the probe was expected to be refused and compiled: {body}"
    message = conftest.panic_message(err)
    assert message is not None, f"refused with no panic of the engine's: {err[:600]}"
    return message


# the wording of one legend line of the example plan Treppenhaus in the three languages
WALL = {"de": "Feuerwiderstand EI 60-RF1", "fr": "Résistance au feu EI 60-RF1", "en": "Fire resistance EI 60-RF1"}
TITLE = {"de": "Legende", "fr": "Légende", "en": "Legend"}
# Typst's own «Abbildung» follows config.typ's doc-lang -- German in the example project -- and not the engine's language
FIGURE = {"de": "Abbildung 1", "fr": "Abbildung 1", "en": "Abbildung 1"}
CAPTION = {"de": "Brandschutzplan Treppenhaus", "fr": "Plan de protection incendie Treppenhaus", "en": "Fire-protection plan Treppenhaus"}


# --- image-fire-plan (spec 2026-10-21-commandes-typst-refonte, REQ-014: #show-fire-plan until then) ----------------------------

FIGURE_OF = '#figure(image-fire-plan("{plan}"{args}), kind: image, caption: [Plan])'


def test_a_fire_plan_prints_in_the_reports_language_with_its_legend():
    here = _project("fire_print_languages")
    for lang in ("de", "fr", "en"):
        text = _text(here, FIGURE_OF.format(plan="Treppenhaus", args=', detail-legend: ("objects", "scale-bar")'), f"lang-{lang}", lang)
        assert TITLE[lang] in text and WALL[lang] in text, (lang, text)
        assert FIGURE[lang] in text, (lang, text)


def test_the_legend_is_taken_off_the_plan_and_nothing_else():
    here = _project("fire_print_legend")
    on = _text(here, FIGURE_OF.format(plan="Treppenhaus", args=', detail-legend: ("objects", "scale-bar")'), "on")
    off = _text(here, FIGURE_OF.format(plan="Treppenhaus", args=', detail-legend: "scale-bar"'), "off")
    assert WALL["de"] in on and WALL["de"] not in off and "Legende" not in off
    assert re.search(r"^0 \d+ m$", on, re.M) and re.search(r"^0 \d+ m$", off, re.M), "the scale bar stays: the plan has a scale"
    bare = _text(here, FIGURE_OF.format(plan="Treppenhaus", args=', detail-legend: "none"'), "bare")
    assert not re.search(r"^0 \d+ m$", bare, re.M), bare


def test_a_plan_following_a_position_plan_has_no_scale_bar_where_that_has_none():
    here = _project("fire_print_following")
    text = _text(here, FIGURE_OF.format(plan="Pavillon-EG", args=', detail-legend: "scale-bar"'), "following")
    assert not re.search(r"^0 \d+ m$", text, re.M) and "ca. 1:" not in text


def test_the_ids_are_the_plans_of_the_export_and_an_unknown_one_is_refused_listing_them():
    here = _project("fire_print_ids")
    assert "Pavillon-EG,Treppenhaus" in _text(here, '#ids("fire-plan").join(",")', "ids")
    # an `assert`: the message is in what Typst prints
    code, err, _ = _run(here, '#image-fire-plan("Nope")', "unknown")
    assert code != 0 and 'image-fire-plan: no plan "Nope" -- valid plans: Pavillon-EG, Treppenhaus' in err, err[:600]
    # an id of the position plans is not one of the fire plans
    code, err, _ = _run(here, '#image-fire-plan("Pavillon")', "position")
    assert code != 0 and 'image-fire-plan: no plan "Pavillon"' in err, err[:600]


# --- a sheet ---------------------------------------------------------------------------------------

def _sheet(here, sheet_id="F01"):
    sheets.new_sheet(here, sheet_id, "A3", True, kind="fire")   # a fire sheet: position plans and fire plans are never on one sheet (v0.116)
    return sheet_id


def _compiled(here, sheet_id):
    _need_typst()
    ok, message = sheets.compile(here, sheet_id)
    assert ok, message
    return _text_of(sheets.pdf(here, sheet_id))


def test_on_a_sheet_the_fire_legend_is_both_possible_on_the_plan_and_as_an_object_of_its_own():
    _need_typst()
    lang = "de"
    for name, on_plan, separate in (("both", True, True), ("plan", True, False), ("object", False, True), ("none", False, False)):
        here = _project(f"fire_print_sheet_{name}")
        sid = _sheet(here)
        assert sheets.language(here) == lang
        sheets.add_fire_viewport(here, sid, "Treppenhaus", 14, 30, scale=100, legend=on_plan)
        if separate:
            sheets.add_fire_legend(here, sid, 250, 30, width=130)
        text = _compiled(here, sid)
        assert len(re.findall(re.escape(WALL[lang]), text)) == int(on_plan) + int(separate), (name, text)
        assert "1:100" in text, "the title block names the scale the fire plan is drawn at"


def test_the_fire_legend_of_a_sheet_lists_the_symbols_of_the_plans_it_shows_and_follows_the_language():
    here = _project("fire_print_sheet_lang")
    sid = _sheet(here)
    sheets.add_fire_viewport(here, sid, "Treppenhaus", 14, 30, scale=100, legend=False)
    sheets.add_fire_viewport(here, sid, "Pavillon-EG", 14, 200, width=60, legend=False)
    sheets.add_fire_legend(here, sid, 250, 30, width=130)
    text = _compiled(here, sid)
    # both plans' symbols, once each: the wall EI 30 the two share is listed once
    assert text.count("Feuerwiderstand EI 30") == 1 and "Feuerwiderstand EI 60-RF1" in text and "Feuerwiderstand EI 60\n" in text + "\n"
    assert "Notausgang" in text and "Türe ohne Feuerwiderstand" in text, "an engine word of the legend, translated by its key"
    # the same sheet in French: the legend's lines say it themselves
    (here.config_typ).write_text(
        re.sub(r'#let doc-lang = "de"', '#let doc-lang = "fr"', (here.config_typ).read_text(encoding="utf-8")), encoding="utf-8")
    source = sheets.path(here, sid)
    source.write_text(source.read_text(encoding="utf-8").replace('set-report-language("de")', 'set-report-language("fr")'), encoding="utf-8")
    french = _compiled(here, sid)
    assert "Résistance au feu EI 60-RF1" in french and "Sortie de secours" in french and "Porte sans résistance au feu" in french, french


def test_a_fire_plan_on_a_sheet_carries_its_scale_bar_when_asked():
    """Issue #9: `sheet-fire-viewport(scale-bar: true)` called `plan-scale-bar` outside any `context` and the sheet did not compile, as `sheet-viewport` did not."""
    here = _project("fire_print_sheet_scale_bar")
    sid = _sheet(here)
    oid = sheets.add_fire_viewport(here, sid, "Treppenhaus", 14, 30, scale=100, legend=False)
    model = sheets.model(here, sid, oid)
    model.set_scale_bar(True)
    sheets.set_object(here, sid, oid, model)
    assert re.search(r"^0 \d+ m$", _compiled(here, sid), re.M)


def test_a_fire_plan_with_no_scale_cannot_be_given_one_and_the_refusal_names_the_fire_tab():
    here = _project("fire_print_sheet_refused")
    sid = _sheet(here)
    sheets.add_fire_viewport(here, sid, "Pavillon-EG", 14, 30, scale=100)
    _need_typst()
    ok, message = sheets.compile(here, sid)
    assert not ok and "sheet-fire-viewport" in message and "fire-protection plan tab" in message, message
    # an id of the position plans, or none at all, is refused naming the fire plans there are
    source = sheets.path(here, sid)
    source.write_text(source.read_text(encoding="utf-8").replace('"Pavillon-EG"', '"Pavillon"').replace("scale: 100", "width: 80mm"), encoding="utf-8")
    ok, message = sheets.compile(here, sid)
    assert not ok and "no fire-protection plan" in message and "Treppenhaus" in message, message


def test_a_sheet_viewport_with_no_plan_draws_the_frame_and_the_two_fire_objects_are_sheet_objects():
    here = _project("fire_print_sheet_frame")
    sid = _sheet(here)
    sheets.add_object(here, sid, "sheet-fire-viewport", to.Call("sheet-fire-viewport", {"x": to.Length(20, "mm"), "y": to.Length(30, "mm"), "width": to.Length(90, "mm")}), base="fire")
    text = _compiled(here, sid)
    assert "[Auszug aus dem Brandschutzplan]" in text
    kinds = [o.type for o in to.objects(sheets.read(here, sid))]
    assert "sheet-fire-viewport" in kinds and "sheet-fire-legend" not in kinds
    assert sheets.add_fire_legend(here, sid, 250, 30) == "fire-legend"
    assert to.find(sheets.read(here, sid), "fire-legend").state == "canonical"
    assert to.find(sheets.read(here, sid), "fire").state == "canonical"


# --- the legend lines ------------------------------------------------------------------------------

def test_the_legend_lines_of_a_fire_plan_say_their_own_wording_and_a_position_plans_go_by_their_key():
    """`plan-legend` reads `engine` before `term` before the STE key: the fire export's lines carry the first two, a position plan's neither."""
    fire = json.loads((project.Project.load(next(SAMPLE.glob("*.woodcore"))).data_dir / "fire.json").read_text(encoding="utf-8"))
    for plan in fire["plans"].values():
        for line in plan["legend_lines"]:
            assert ("engine" in line) != ("term" in line), line
    calc = conftest.engine_source()
    assert re.search(r'if "engine" in l \{ t-str\(l\.engine\) \}\s*else if "term" in l \{ tl-str\(l\.term\) \}', calc)
    plans = json.loads((project.Project.load(next(SAMPLE.glob("*.woodcore"))).data_dir / "plans.json").read_text(encoding="utf-8"))
    for plan in plans["plans"].values():
        if isinstance(plan["legend"], list):
            assert all("engine" not in l and "term" not in l for l in plan["legend"])
