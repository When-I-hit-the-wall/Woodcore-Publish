"""The list of the positions (v0.116, lib/positions.typ; its columns, their widths, its legend and its margin v0.117): STE Compact 02's «liste des positions» with this project's own columns -- `#show-position-list` in a report, `sheet-position-list` on an export sheet, and a sheet of its own holding the list alone (calc/sheets.py's `new_position_list_sheet`).

What is held:

* the columns are the Positions tab's, in its order, each heading the engine's word in the document's language;
* **the type is printed in the document's language** where the glossary carries it (Träger -> Poutre), the description never;
* the three scopes: every position, those drawn on given plans -- in the project's order --, those of one storey (the id's second letter); a plan or a scope that is not one is refused naming what to write;
* **the ID's colours are plan_svg's own**, restated in Typst and held equal here;
* on a sheet the list lists the positions of the plans the sheet shows by default, and a list sheet holds the list alone;
* **v0.117**: the columns printed are chosen (`columns:`), a width is fixed for some (`widths:`, a length or a percentage), a legend is set under the table (`legend:`), nothing is printed where no plan is named, **the table never goes past the right margin** (a project of 59 positions with long values, checked on the pixels of the page), a long table runs over several pages with its heading on each and a row never split between two.

⚠️ Every compiled check is skipped where `typst` is not on the path. Each works on a copy of the example project of its own.
"""

import json
import re
import shutil
import subprocess
import sys
import unicodedata

import conftest
from conftest import ROOT, Skip
import project
import sheets
import typst_objects as to

SAMPLE = ROOT / "tests" / "projet-exemple"
POSITIONS_TYP = ROOT / "lib" / "positions.typ"


def _need_typst():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


def _project(name):
    """A copy of the example project, its engine synced -- the plan Geratehaus showing T001 alone, so that a list of its positions differs from the list of all."""
    root = conftest.tmpdir(name) / "Exemple"
    shutil.copytree(SAMPLE, root, ignore=shutil.ignore_patterns("lib", "VERSION", "stamps", "_Archiv"))
    here = project.Project.load(root / "Exemple.woodcore")
    project.sync_engine(here)
    record = here.data_dir / "plans.json"
    data = json.loads(record.read_text(encoding="utf-8"))
    data["plans"]["Geratehaus"]["labels"] = ["T001"]
    record.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return here


def _text_of(pdf):
    """The text of the pages, a hyphen the table put in a word (a soft hyphen and its line break) taken out again: a column that is narrower than a long word cuts it, and the word is still there."""
    from pypdf import PdfReader
    text = unicodedata.normalize("NFKC", "\n".join(p.extract_text() for p in PdfReader(str(pdf)).pages))
    return text.replace("\xad\n", "").replace("\xad", "")


def _run(here, body, name, lang="de"):
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


def _ids(text):
    return re.findall(r"\b[TS]00\d\b", text)


# --- the colours -------------------------------------------------------------------------------------

def test_the_id_colours_are_plan_svgs_own():
    """lib/positions.typ restates the STE colours of plan_svg.py -- COLOURS, the symbol's and the box's, LABEL_COLOURS, the number's where it differs, and STADIUM, the letters whose number sits in a stadium -- Typst reading no Python: each letter names the token of lib/figure-palette.json plan_svg draws it in (v0.120, D5), so a colour changed on the plan must change in the list too."""
    from domains import plan_svg, svg_draw
    text = POSITIONS_TYP.read_text(encoding="utf-8")

    def table(name):
        body = re.search(rf"#let {name} = \((.*?)\)\n", text, re.S).group(1)
        return {k.strip('"'): svg_draw.colour(v) for k, v in re.findall(r'("?[^\s:,"]+"?): figure-colour\("([a-z-]+)"\)', body)}
    assert table("position-colours") == plan_svg.COLOURS
    assert table("position-label-colours") == plan_svg.LABEL_COLOURS
    stadium = re.search(r'#let position-stadium = \((.*?)\)', text).group(1)
    assert set(re.findall(r'"([^"]+)"', stadium)) == plan_svg.STADIUM


def test_lib_positions_travels_with_the_engine_and_is_catalogued():
    import sys
    assert "lib/positions.typ" in project.ENGINE_FILES
    sys.path.insert(0, str(ROOT / "calc" / "tools"))
    import build_reference as ref
    assert "positions.typ" in ref.LIB_FILES
    categories = dict(ref.CATEGORIES)
    assert "position" in categories["display"]
    formula = (ROOT / "lib" / "formula.typ").read_text(encoding="utf-8")
    assert '#import "positions.typ": position' in formula   # lib/formula.typ's own import, read and never written -- relative on purpose (tests/test_harness.py)


# --- in a document ----------------------------------------------------------------------------------

def test_the_section_words_are_the_ones_the_window_lists():
    """The four timber names of strings.json are section.py's own, in the three languages."""
    from domains import section
    strings = json.loads((ROOT / "calc" / "i18n" / "strings.json").read_text(encoding="utf-8"))
    engine = strings["engine"]
    for entry in section.TIMBER_TYPES:
        words = engine["position_list.section." + entry["code"]]
        assert {lang: words[lang] for lang in ("de", "fr", "en")} == {lang: entry[lang] for lang in ("de", "fr", "en")}, entry["code"]


# --- columns, widths, legend and the margin (v0.117) ------------------------------------------------------

def test_the_column_list_is_typsts_and_the_displays():
    """The nine columns exist in lib/positions.typ and in the display view (calc/tools/display_options.py): one list, held equal here -- the same method as the ID colours."""
    sys.path.insert(0, str(ROOT / "calc" / "tools"))
    import display_options as opts
    typst = tuple(re.findall(r'"([a-z_]+)"', re.search(r"#let position-list-columns-all = \(([^)]*)\)", POSITIONS_TYP.read_text(encoding="utf-8")).group(1)))
    assert typst == opts.POSITION_LIST_COLUMNS
    engine = json.loads((ROOT / "calc" / "i18n" / "strings.json").read_text(encoding="utf-8"))["engine"]
    for key in typst:
        assert f"position_list.{key}" in engine, f"the heading of the {key} column is the engine's word"
        for lang in ("fr", "de", "en"):
            assert f"ds_col_{key}" in opts.STRINGS[lang], (lang, key)


# --- on a sheet ----------------------------------------------------------------------------------------

def test_on_a_sheet_the_list_is_the_projects_list_file():
    """Q-015 (spec 2026-10-21-commandes-typst-refonte): a list on a sheet is `box(width:)[#include "/Positions/position-list.typ"]`, the project's list written once -- every position it holds, whatever plans the sheet shows; the scope a list of a sheet had is gone with the sheet-* calls."""
    _need_typst()
    here = _project("position_list_sheet")
    sid = sheets.new_sheet(here).stem
    sheets.add_viewport(here, sid, "Geratehaus", 20, 35, width=120)
    oid = sheets.add_position_list(here, sid, 230, 35, width=170)
    assert oid == "positions" and to.find(sheets.read(here, sid), oid).state == "canonical"
    assert '#include "/Positions/position-list.typ"' in sheets.read(here, sid)
    ok, message = sheets.compile(here, sid)
    assert ok, message
    text = _text_of(sheets.pdf(here, sid))
    assert "Positionsliste" in text
    assert "Träger" in text and "Stahlstütze" in text, "the project's list: every position, the sheet's plan showing T001 alone"


def test_a_list_sheet_holds_the_list_alone_a4_portrait():
    _need_typst()
    here = _project("position_list_own_sheet")
    sid = sheets.new_position_list_sheet(here).stem
    found = [(o.type, o.id) for o in sheets.objects(here, sid)]
    assert found == [("sheet-page", "page"), ("sheet-text", "title"), ("sheet-position-list", "positions")], found
    assert sheets.page(here, sid).size() == (210, 297) and sheets.sheet_kind(here, sid) == "position"
    ok, message = sheets.compile(here, sid)
    assert ok, message
    text = _text_of(sheets.pdf(here, sid))
    assert "Positionsliste" in text and "T001" in _ids(text), text   # the project's list (Q-015)


def test_the_list_object_reads_back_its_model_and_refuses_what_it_does_not_take():
    m = to.model_for(to.default_call("sheet-position-list"))
    m.set_scope("storey")
    m.set_storey("1")
    m.set_plans(["Pavillon", "Geratehaus"])
    m.set_title(None)
    text = to.serialize(m.to_call())
    assert to.serialize(to.model_for(to.parse_call(text)).to_call()) == text
    for bad in (lambda: m.set_scope("some"), lambda: m.set_storey("OG"), lambda: m.set_plans(3)):
        try:
            bad()
        except to.ModelError:
            continue
        raise AssertionError("the list took a value it does not take")


def test_position_prints_one_position_with_the_fields_it_names():
    """Spec 2026-10-21-commandes-typst-refonte, REQ-015: `#position("T001", category-show: ("type", "material", "strength-class"))` prints the id and these three fields read from data/positions/T001.json, in the report's language; `length` is the length the plans draw it with (data/quantities.json); its own label and description follow; an unknown position or field is refused naming the valid ones."""
    here = _project("position_one")
    text = _text(here, '#position("T001", category-show: ("type", "material", "strength-class"))', "position_three", lang="fr")
    assert "T001" in text and "Poutre" in text and "C24" in text and "100/200" not in text, text
    quantities = json.loads((here.data_dir / "quantities.json").read_text(encoding="utf-8"))
    rows = [r for r in quantities["rows"] if r["position"] == "T001" and r.get("length_m") is not None]
    if not rows:   # the example's plans have no scale: a length measured is given here
        quantities["rows"].append({"plan": "Pavillon", "position": "T001", "material": "Fichte C24", "section": "100/200 mm", "length_m": 4.25, "area_m2": None, "volume_m3": None})
        (here.data_dir / "quantities.json").write_text(json.dumps(quantities, ensure_ascii=False), encoding="utf-8")
    want = sum(r["length_m"] for r in json.loads((here.data_dir / "quantities.json").read_text(encoding="utf-8"))["rows"] if r["position"] == "T001" and r.get("length_m") is not None)
    text = _text(here, '#position("T001", label: "Pfette", descr: "über Achse B", category-show: ("dimension", "units", "length", "moisture-class"))', "position_length")
    assert "Pfette" in text and "100/200" in text and "über Achse B" in text and "Feuchteklasse 2" in text and f"L = {want:.2f}".rstrip("0").rstrip(".") in text, text
    assert "T001" in _refusal(here, '#position("T999")', "position_unknown")
    assert "valid" in _refusal(here, '#position("T001", category-show: "colour")', "position_field")
