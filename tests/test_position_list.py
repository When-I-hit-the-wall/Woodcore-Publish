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
    probe.write_text('#import "/config.typ": conf\n#import "/commands.typ": *\n#show: conf\n'
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
    """lib/positions.typ restates the STE colours of plan_svg.py -- COLOURS, the symbol's and the box's, LABEL_COLOURS, the number's where it differs, and STADIUM, the letters whose number sits in a stadium -- Typst reading no Python: a colour changed on the plan must change in the list too."""
    from domains import plan_svg
    text = POSITIONS_TYP.read_text(encoding="utf-8")

    def table(name):
        body = re.search(rf"#let {name} = \((.*?)\)\n", text, re.S).group(1)
        return {k.strip('"'): v for k, v in re.findall(r'("?[^\s:,"]+"?): "(#[0-9A-Fa-f]{6})"', body)}
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
    assert "show-position-list" in categories["display"] and "sheet-position-list" in categories["sheets"]
    formula = (ROOT / "lib" / "formula.typ").read_text(encoding="utf-8")
    assert '#import "positions.typ": show-plan-quantities, show-position-list' in formula   # lib/formula.typ's own import, read and never written -- relative on purpose (tests/test_harness.py)


# --- in a document ----------------------------------------------------------------------------------

def test_every_position_is_listed_with_the_positions_tabs_columns_in_the_documents_language():
    here = _project("position_list_all")
    german = _text(here, "#show-position-list()", "all-de")
    # nine columns do not fit an A4 portrait page at their least: the table keeps to the margin (v0.117) and a long heading is cut at a hyphen (soft hyphen and line break are dropped here)
    plain = german.replace("\xad\n", "")
    for heading in ("Positionsliste", "ID", "Typ", "Material", "Feuchteklasse", "Beschreibung"):
        assert heading in plain, (heading, german)
    assert _ids(german) == ["T001", "S001", "S002"], "in the project's order"
    assert "Träger" in german and "Stütze" in german and "C24" in german and "S355" in german and "101.6x10" in german
    french = _text(here, "#show-position-list()", "all-fr", "fr")
    assert "Liste des positions" in french and "Matériau" in french
    assert "Poutre" in french and "Poteau" in french and "Träger" not in french, "the type follows the document's language"
    assert "Stahlstütze" in french, "the description is the engineer's own words and is never translated"
    english = _text(here, "#show-position-list(title: [Our positions])", "all-en", "en")
    assert "Our positions" in english and "Beam" in english and "Moisture class" in " ".join(english.split()), "a heading set on two lines"


def test_the_section_type_is_printed_as_a_word_in_the_documents_language_and_a_steel_family_as_its_code():
    """v0.116: the «Type de section» column printed the stored code («rec»); it prints the word -- the names calc/domains/section.py lists, in `strings.json` -- and a steel family (ROR) stays its designation."""
    here = _project("position_list_section_words")
    german = _text(here, '#show-position-list(title: none)', "sec-de")
    assert "Rechteckquerschnitt" in " ".join(german.split()) and "ROR" in german and " rec " not in german, german
    french = _text(here, '#show-position-list(title: none)', "sec-fr", "fr")
    assert "Section rectangulaire" in " ".join(french.split()) and "ROR" in french, french
    english = _text(here, '#show-position-list(title: none)', "sec-en", "en")
    assert "Rectangular section" in " ".join(english.split()) and "ROR" in english, english


def test_the_section_words_are_the_ones_the_window_lists():
    """The four timber names of strings.json are section.py's own, in the three languages."""
    from domains import section
    strings = json.loads((ROOT / "calc" / "i18n" / "strings.json").read_text(encoding="utf-8"))
    engine = strings["engine"]
    for entry in section.TIMBER_TYPES:
        words = engine["position_list.section." + entry["code"]]
        assert {lang: words[lang] for lang in ("de", "fr", "en")} == {lang: entry[lang] for lang in ("de", "fr", "en")}, entry["code"]


def test_the_positions_of_given_plans_or_of_one_storey():
    here = _project("position_list_scopes")
    on_plan = _text(here, '#show-position-list(scope: "plans", plans: "Geratehaus", title: none)', "plans")
    assert _ids(on_plan) == ["T001"], on_plan
    both = _text(here, '#show-position-list(scope: "plans", plans: ("Geratehaus", "Pavillon"), title: none)', "plans-two")
    assert _ids(both) == ["T001", "S001", "S002"], "each once, in the project's order"
    storey = _text(here, '#show-position-list(scope: "storey", storey: "0", title: none)', "storey")
    assert _ids(storey) == ["T001", "S001", "S002"]
    none = _text(here, '#show-position-list(scope: "storey", storey: "1")', "storey-none")
    assert "Keine Position." in none and not _ids(none)


def test_no_plan_named_or_ticked_prints_nothing_and_is_no_error():
    """Woodcore's display view leaves `plans:` out when no plan is ticked: that call used to be refused, and the window showed the refusal (v0.117, the engineer: «il ne doit y avoir aucun affichage»)."""
    here = _project("position_list_no_plans")
    engine = json.loads((ROOT / "calc" / "i18n" / "strings.json").read_text(encoding="utf-8"))["engine"]
    caption = {"title": engine["position_list.title"]["de"], "empty": engine["position_list.empty"]["de"]}
    for body, name in (('#show-position-list(scope: "plans")', "no-plans"), ('#show-position-list(scope: "plans", plans: ())', "no-plans-empty"),
                       ('#show-position-list(scope: "plans", plans: "")', "no-plans-text")):
        text = _text(here, body, name)
        assert not _ids(text), (body, text)
        assert caption["title"] not in text and caption["empty"] not in text, f"{body}: a caption or a message was printed: {text!r}"
    # a storey that holds nothing still says so: only the unnamed plans print nothing
    assert caption["empty"] in _text(here, '#show-position-list(scope: "storey", storey: "1")', "storey-none-again")


def test_a_scope_a_plan_or_a_storey_that_is_not_one_is_refused_naming_what_to_write():
    here = _project("position_list_refused")
    message = _refusal(here, '#show-position-list(scope: "everything")', "bad-scope")
    assert message.startswith("show-position-list: scope:") and '"plans"' in message, message
    message = _refusal(here, '#show-position-list(scope: "plans", plans: "Nowhere")', "bad-plan")
    assert "no position plan" in message and "Pavillon" in message, message
    message = _refusal(here, '#show-position-list(scope: "storey", storey: "OG")', "bad-storey")
    assert "numbering character" in message, message


# --- columns, widths, legend and the margin (v0.117) ------------------------------------------------------

def _many(here, count=59):
    """`count` positions of long, unbreakable values, so that the table cannot fit its page by luck: T001 to T0<count>, the project's index naming them in this order. Each description ends with its own marker, so that a row cut between two pages can be found."""
    folder = here.data_dir / "positions"
    ids = [f"T{n:03d}" for n in range(1, count + 1)]
    for n, id in enumerate(ids, 1):
        record = json.loads((folder / "T001.json").read_text(encoding="utf-8"))
        record.update({"position": id, "material": "Brettschichtholz-Verbundwerkstoff", "strength_class": "GL24h-Festigkeitsklasse",
                       "type": "Deckenbalken-Hauptträger", "dimension": "1000/2000",
                       "description": f"Beschreibung-Nr-{n:03d} mit einem langen Text, der in der Zelle über mehrere Zeilen umbrochen werden muss, "
                                      f"Pavillon-Stahlstützenkonstruktion-Erdgeschoss Ende{n:03d}"})
        (folder / f"{id}.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    (here.data_dir / "positions-index.json").write_text(json.dumps({"schema_version": "1.0", "positions": ids}), encoding="utf-8")
    return ids


def _pages(here, body, name, lang="de"):
    """The compiled pages as (text per page, the rightmost pixel that is not white per page at 72 ppi)."""
    from PIL import Image
    from pypdf import PdfReader
    code, err, out = _run(here, body, name, lang)
    assert code == 0, err
    texts = [unicodedata.normalize("NFKC", p.extract_text()).replace("\xad\n", "").replace("\xad", "") for p in PdfReader(str(out)).pages]
    pattern = out.parent / "page-{p}.png"
    run = subprocess.run([project.typst_executable(), "compile", "--root", str(here.typst_root), "--format", "png", "--ppi", "72",
                          str(out.parent / "probe.typ"), str(pattern)], capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert run.returncode == 0, run.stderr
    right = []
    for n in range(1, len(texts) + 1):
        image = Image.open(str(pattern).replace("{p}", str(n))).convert("L")
        width, height = image.size
        # the text area only: the page's own head and foot (a rule, a page number) are not the table's
        top, bottom = round(3.0 * 72 / 2.54) + 4, height - round(2.5 * 72 / 2.54) - 4
        columns = [x for x in range(width) if image.crop((x, top, x + 1, bottom)).getextrema()[0] < 250]
        right.append(max(columns) if columns else 0)
    return texts, right


def _starts(pdf, words):
    """The x of the first glyph run of each of `words` on page 1, from the PDF -- where a column begins."""
    from pypdf import PdfReader
    found = {}

    def visit(text, cm, tm, font, size):
        word = text.strip()
        if word in words and word not in found:
            found[word] = tm[4] * cm[0] + cm[4]

    PdfReader(str(pdf)).pages[0].extract_text(visitor_text=visit)
    return found


def test_the_columns_printed_are_the_ones_named_in_the_order_given():
    here = _project("position_list_columns")
    german = _text(here, '#show-position-list(columns: ("id", "dimension", "description"), title: none)', "cols")
    for kept in ("ID", "Abmessung", "Beschreibung", "100/200", "UK"):
        assert kept in german, (kept, german)
    for dropped in ("Material", "Fichte", "C24", "Feuchte", "Träger"):
        assert dropped not in german, (dropped, german)
    assert german.index("ID") < german.index("Abmessung") < german.index("Beschreibung")
    reversed_ = _text(here, '#show-position-list(columns: ("description", "id"), title: none)', "cols-reversed")
    assert reversed_.index("Beschreibung") < reversed_.index("ID"), "the order is the one given"


def test_a_columns_width_is_a_length_or_a_percentage_of_the_text_width():
    here = _project("position_list_widths")
    code, err, out = _run(here, '#show-position-list(columns: ("id", "type", "material"), widths: (id: 30mm, type: 20%), title: none)', "widths")
    assert code == 0, err
    at = _starts(out, {"ID", "Typ", "Material"})
    assert abs((at["Typ"] - at["ID"]) - 30 * 72 / 25.4) < 1.5, ("the ID column is 30 mm", at)
    # the text area of the report is 21 cm less 2 x 2.5 cm: 20 % of it
    assert abs((at["Material"] - at["Typ"]) - 0.2 * (595.28 - 2 * 70.87)) < 1.5, ("the type column is 20 % of the text width", at)


def test_a_legend_is_set_under_the_table_as_written_and_only_when_there_is_one():
    here = _project("position_list_legend")
    with_legend = _text(here, '#show-position-list(legend: [Die Masse sind in mm: Pavillon + Gerätehaus.])', "legend")
    assert "Die Masse sind in mm: Pavillon + Gerätehaus." in " ".join(with_legend.split())
    assert with_legend.index("Beschreibung") < with_legend.index("Die Masse sind"), "under the table"
    # words the glossary knows are not looked up in a legend: it is the engineer's text
    glossary = _text(here, '#show-position-list(legend: "Träger")', "legend-str")
    assert glossary.count("Träger") == 1 + 1, "the beam's type, and the legend as written"
    assert "Die Masse" not in _text(here, "#show-position-list()", "legend-none")


def test_a_column_or_a_width_that_is_not_one_stops_the_report_naming_it():
    here = _project("position_list_refuse_columns")
    cases = (
        ('#show-position-list(columns: ("id", "nope"))', ("columns:", '"nope"', "valid:", "strength_class")),
        ('#show-position-list(columns: ())', ("columns:", "no column")),
        ('#show-position-list(columns: ("id", "id"))', ("columns:", "twice")),
        ('#show-position-list(columns: "id")', ("columns:", "array")),
        ('#show-position-list(widths: (nope: 10mm))', ("widths:", '"nope"', "valid:")),
        ('#show-position-list(widths: (id: "wide"))', ("widths:", "id", "length")),
        ('#show-position-list(widths: (id: 0mm))', ("widths:", "id")),
        ('#show-position-list(widths: (type: 120%))', ("widths:", "type", "100%")),
        ('#show-position-list(widths: (10mm,))', ("widths:", "dictionary")),
        ('#show-position-list(legend: 5)', ("legend:",)),
    )
    for n, (body, words) in enumerate(cases):
        message = _refusal(here, body, f"refuse-{n}")
        assert message.startswith("show-position-list:"), message
        for word in words:
            assert word in message, (body, word, message)


def test_the_table_never_goes_past_the_right_margin_and_runs_over_several_pages_with_whole_rows():
    here = _project("position_list_margin")
    ids = _many(here)
    texts, right = _pages(here, "#show-position-list()", "many")
    limit = 595.28 - 70.87   # the page less the right margin of 2.5 cm
    assert len(texts) >= 3, f"59 positions of long values fit {len(texts)} page(s)"
    assert max(right) <= limit + 2, f"the table reaches x = {max(right)} on a text area ending at {limit:.1f}: {right}"
    # the heading is set again on every page the table runs onto
    assert all("Beschreibung" in page for page in texts), [("Beschreibung" in page) for page in texts]
    # a row is never cut between two pages: a position and the end of its description are on the same page
    where = {}
    for number, page in enumerate(texts):
        for id in ids:
            if re.search(rf"\b{id}\b", page):
                where[id] = number
    for n, id in enumerate(ids, 1):
        ends = [number for number, page in enumerate(texts) if f"Ende{n:03d}" in page.replace("\n", "")]
        assert ends == [where[id]], f"{id} is on page {where[id] + 1}, the end of its description on {[e + 1 for e in ends]}"
    # the same, with widths that are stated: the margin still holds
    texts2, right2 = _pages(here, '#show-position-list(widths: (id: 25mm, type: 30%, description: 40%))', "many-widths")
    assert max(right2) <= limit + 2, f"with widths the table reaches x = {max(right2)}: {right2}"


def test_widths_that_do_not_fit_the_text_are_reduced_and_the_report_says_so():
    here = _project("position_list_over")
    text = _text(here, '#show-position-list(widths: (id: 120mm, type: 120mm, material: 60mm))', "over")
    assert "Spaltenbreiten" in text and "verkleinert" in text, text
    fitting = _text(here, '#show-position-list(widths: (id: 20mm))', "fits")
    assert "Spaltenbreiten" not in fitting
    french = _text(here, '#show-position-list(widths: (id: 120mm, type: 120mm, material: 60mm))', "over-fr", "fr")
    assert "réduites" in " ".join(french.split()), french


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

def test_on_a_sheet_the_list_lists_the_positions_of_the_sheets_plans():
    _need_typst()
    here = _project("position_list_sheet")
    sid = sheets.new_sheet(here).stem
    sheets.add_viewport(here, sid, "Geratehaus", 20, 35, width=120)
    oid = sheets.add_position_list(here, sid, 230, 35, width=170)
    assert oid == "positions" and to.find(sheets.read(here, sid), oid).state == "canonical"
    ok, message = sheets.compile(here, sid)
    assert ok, message
    text = _text_of(sheets.pdf(here, sid))
    assert "Positionsliste" in text
    assert "Träger" in text and "Stahlstütze" not in text, "the sheet's plan shows T001 alone"
    # every position, once the scope says so
    sheets.set_object(here, sid, oid, _scoped(here, sid, oid, "all"))
    ok, message = sheets.compile(here, sid)
    assert ok, message
    assert "Stahlstütze" in _text_of(sheets.pdf(here, sid))


def _scoped(here, sid, oid, scope):
    m = sheets.model(here, sid, oid)
    m.set_scope(scope)
    return m


def test_a_list_sheet_holds_the_list_alone_a4_portrait():
    _need_typst()
    here = _project("position_list_own_sheet")
    sid = sheets.new_position_list_sheet(here, plans=["Geratehaus"]).stem
    found = [(o.type, o.id) for o in sheets.objects(here, sid)]
    assert found == [("sheet-page", "page"), ("sheet-text", "title"), ("sheet-position-list", "positions")], found
    assert sheets.page(here, sid).size() == (210, 297) and sheets.sheet_kind(here, sid) == "position"
    model = sheets.model(here, sid, "positions")
    assert model.get("plans") == ["Geratehaus"] and model.get("scope") == "plans" and model.get("title") is None
    ok, message = sheets.compile(here, sid)
    assert ok, message
    text = _text_of(sheets.pdf(here, sid))
    assert "Positionsliste" in text and _ids(text) == ["T001"], text
    # with no plan named, every position
    other = sheets.new_position_list_sheet(here).stem
    assert sheets.model(here, other, "positions").get("scope") == "all"


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
