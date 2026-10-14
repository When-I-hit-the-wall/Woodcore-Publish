"""The parametric objects of a project's documents (lib/document.typ, the three document modes, phase 3): the ten commands Woodcore writes between the tags of a section of the convention d'utilisation, the base de projet and the report.

What is held, command by command, is what each one decides and nothing `render-table` is already held to:

* a table prints its rows, and **a hidden column is absent** from the page while its cells stay in the call;
* **the engineer's words are never translated** -- a cell, a title, a caption that happens to be a term of the glossary («Schneelast») or to match a template of it («Element 3») prints as it is written, in a French report as in a German one;
* a live-load cell left to `auto` **is the export's own q_k and Q_k** for the row's category, a number written there **is printed in orange** with the line saying what orange means, and category E -- which SIA 261 8.2.2 leaves to the project -- is refused at `auto`;
* **no ψ column, ever** (the engineer, 01.10.2026: the Reduktionsbeiwerte are never shown for live loads): the default columns are the six, a column of the id `psi_0` is no known column and is refused, and a planted export that still carries ψ vars prints none of them;
* the load column of the non-structural self-weight takes a `#val(...)`, printed as the export's value;
* the field's placeholder, the ticked boxes, the chosen answer, the picture's frame, the plan's frame, the signature rows and the norms listed in full -- and registered for the bibliography;
* **every malformed argument is refused with a panic naming the command**, read with `conftest.panic_message`;
* and the file is where the engine says it is: `project.ENGINE_FILES`, `build_reference.LIB_FILES`, the `objects` category, and imported by name, so a helper never reaches a section.

⚠️ Every compiled check is skipped where `typst` is not on the path. Where a probe needs an export the example project does not carry -- a planted one -- it works on a copy of the report folder and the generated folder of its own (`_root`), test_display.py's own arrangement, so nothing the rest of the suite reads changes under it.
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

PROJECT = conftest.PROJECT
DOCUMENT_TYP = ROOT / "lib" / "document.typ"
COMMANDS = ("doc-table", "live-load-table", "dead-load-table", "doc-field", "doc-checklist", "doc-choice",
            "doc-image", "doc-plan", "doc-fire-plan", "doc-extract", "doc-annexes", "doc-signatures", "show-norm-list", "doc-value")
# The report's orange for a value written over (calc-engine.typ's override-colour, the Katalog's OVERRIDE_COLOR).
ORANGE = "#b35c00"


def _guard():
    if not conftest.have_typst():
        raise Skip("typst is not on the path")


def _root(name):
    """A copy of the example project's top files and its generated folder -- the engine and the export: a Typst root of this test's own."""
    d = conftest.tmpdir(name)
    for f in ("commands.typ", "config.typ"):
        shutil.copyfile(PROJECT.typst_root / f, d / f)
    relative = PROJECT.generated_dir.relative_to(PROJECT.typst_root)
    shutil.copytree(PROJECT.generated_dir, d / relative,
                    copy_function=shutil.copyfile, ignore=shutil.ignore_patterns("out", "docs"))
    images = PROJECT.typst_root / "Images"
    if images.is_dir():
        shutil.copytree(images, d / "Images", copy_function=shutil.copyfile)
    return d, d / relative / "data"


def _run(root, body, name, fmt="pdf", lang="de"):
    _guard()
    d = root / ".probe" / name
    d.mkdir(parents=True, exist_ok=True)
    probe = d / "probe.typ"
    probe.write_text('#import "/config.typ": conf\n#import "/commands.typ": *\n#show: conf\n'
                     f'#set-report-language("{lang}")\n' + body + "\n", encoding="utf-8")
    out = d / f"probe.{fmt}"
    run = subprocess.run(["typst", "compile", "--root", str(root), "--format", fmt, str(probe), str(out)],
                         capture_output=True, text=True, encoding="utf-8", errors="replace")
    return run.returncode, run.stderr, out


def _text(body, name, lang="de", root=None):
    """The probe's text, as pypdf reads it back. NFKC: math's letters read as letters, «…» as «...», ² as 2."""
    root = root or PROJECT.typst_root
    code, err, out = _run(root, body, name, lang=lang)
    assert code == 0, err
    from pypdf import PdfReader
    return unicodedata.normalize("NFKC", "\n".join(p.extract_text() for p in PdfReader(str(out)).pages))


def _svg(body, name):
    code, err, out = _run(PROJECT.typst_root, body, name, fmt="svg")
    assert code == 0, err
    return out.read_text(encoding="utf-8").lower()


def _refusal(body, name):
    """The message a refused probe panics with."""
    code, err, _ = _run(PROJECT.typst_root, body, name)
    assert code != 0, f"the probe was expected to be refused and compiled: {body}"
    message = conftest.panic_message(err)
    assert message is not None, f"refused with no panic of the engine's: {err[:600]}"
    return message


def _num(x):
    """A number as the engine prints it: at most three decimals, trailing zeros dropped (fmt-decimals)."""
    s = f"{float(x):.3f}".rstrip("0").rstrip(".")
    return s.replace("-", "−")


def _live(category):
    return conftest.exported("calculations.json")["domains"]["live-load"]["instances"][category]["vars"]


LIVE_TABLE = """#live-load-table(
  hidden: ("zone",),
  rows: (
    (storey: [EG], use: [Büro], category: "B", q_k: auto, Q_k: auto),
    (storey: [Dach], use: [Unterhalt], category: "H", q_k: auto, Q_k: auto),
  ),
)"""


# --- where the file is -----------------------------------------------------------------------

def test_the_file_is_where_the_engine_says_it_is():
    """lib/document.typ is copied into every project (`project.ENGINE_FILES`), catalogued (`build_reference.LIB_FILES`) and its thirteen commands are the `objects` category -- a file one of them forgets is a report that fails on «file not found» in a project and nowhere in the checkout."""
    sys.path.insert(0, str(ROOT / "calc" / "tools"))
    import build_reference as ref
    assert "lib/document.typ" in project.ENGINE_FILES
    assert "document.typ" in ref.LIB_FILES
    assert tuple(dict(ref.CATEGORIES)["objects"]) == COMMANDS
    formula = (ROOT / "lib" / "formula.typ").read_text(encoding="utf-8")
    line = next(l for l in formula.splitlines() if l.startswith('#import "document.typ":'))      # relative on purpose: the line of lib/formula.typ that is looked for, not an import a probe writes
    assert sorted(n.strip() for n in line.split(":", 1)[1].split(",")) == sorted(COMMANDS), line


def test_a_helper_does_not_reach_a_section():
    """formula.typ imports the ten commands by name, so `doc-refuse` and the other helpers are the file's own -- a section that names one is refused as an unknown variable."""
    code, err, _ = _run(PROJECT.typst_root, '#doc-refuse("x", "y")', "helper")
    assert code != 0 and "unknown variable: doc-refuse" in err, err


def test_the_file_reads_no_norm_file_of_its_own():
    """The live loads come out of the export and the norms out of norms.json through bibliography.typ: document.typ names no file of calc/norms/, which test_distance.py holds equal to ENGINE_FILES."""
    source = DOCUMENT_TYP.read_text(encoding="utf-8")
    assert "calc/norms" not in re.sub(r"//.*", "", source), "lib/document.typ reads a norm file of its own"
    assert "json(" not in re.sub(r"//.*", "", source)


# --- doc-table --------------------------------------------------------------------------------

def test_a_table_prints_its_rows_and_leaves_a_hidden_column_out():
    body = """#doc-table(
  columns: (
    (id: "part", title: [Bauteil]),
    (id: "years", title: [Nutzungsdauer], unit: "Jahre", kind: "number"),
    (id: "remark", title: [Bemerkung], kind: "wide"),
  ),
  hidden: ("remark",),
  rows: (
    (part: [Tragwerk], years: 50, remark: [Unsichtbarer Vermerk]),
    (part: [Fassade], years: -25),
  ),
  caption: [Geplante Nutzungsdauer],
)"""
    text = _text(body, "table")
    assert "Geplante Nutzungsdauer" in text and "Bauteil" in text and "[Jahre]" in text, text
    assert "Tragwerk 50" in text, text
    assert "Fassade −25" in text, text      # a number with a real minus sign
    assert "Bemerkung" not in text and "Unsichtbarer Vermerk" not in text, text


def test_a_table_without_its_heading_row():
    body = """#doc-table(
  columns: ((id: "item", title: [Element]), (id: "text", title: [Beschreibung], kind: "wide")),
  rows: ((item: [Bauherrschaft], text: [[…]]), (item: [Standort], text: "Parzelle 12")),
  header: false,
)"""
    text = _text(body, "keyvalue")
    assert "Bauherrschaft [...]" in text and "Standort Parzelle 12" in text, text
    assert "Element" not in text and "Beschreibung" not in text, text


def test_a_table_with_no_column_or_every_column_hidden_prints_nothing():
    text = _text('Vorher\n#doc-table()\n#doc-table(columns: ((id: "a", title: [A]),), hidden: ("a",), rows: ((a: [x]),))\nNachher', "empty")
    assert "Vorher" in text and "Nachher" in text and "x" not in text.replace("Nachher", ""), text


def test_the_engineers_words_are_never_translated():
    """«Schneelast» is a term of the glossary and «Element 3» matches its template «Element {n}»: in a French report the export's own words would come out «Charge de neige» and «Élément 3». The engineer's -- a title, a cell, a caption, a string as much as content -- must not."""
    body = """#doc-table(
  columns: ((id: "a", title: "Schneelast"), (id: "b", title: [Element 3])),
  rows: ((a: "Schneelast", b: "Element 3"),),
  caption: "Schneelast",
)
#live-load-table(columns: ((id: "use", title: "Schneelast"), (id: "category")), rows: ((use: "Element 3", category: "B"),))"""
    text = _text(body, "words", lang="fr")
    assert "Charge de neige" not in text and "Élément" not in text and "élément" not in text, text
    assert text.count("Schneelast") == 4 and text.count("Element 3") == 3, text


# --- live-load-table --------------------------------------------------------------------------

def test_an_auto_live_load_cell_is_the_exports_value():
    """`auto` reads the category's q_k and Q_k out of the export -- `val("q_k", domain: ("live-load", cat))` -- so the table follows SIA 261 Tabelle 8 and never types a value twice."""
    b, h = _live("B"), _live("H")
    text = _text(LIVE_TABLE, "auto")
    assert f"EG Büro B {_num(b['q_k']['value'])} {_num(b['Q_k']['value'])}" in text, text
    assert f"Dach Unterhalt H {_num(h['q_k']['value'])} {_num(h['Q_k']['value'])}" in text, text


def test_the_default_columns_are_the_six_and_none_is_a_psi():
    """The known columns carry their own heading in the report's language -- the six of `live-load-columns` -- and nothing hides by default: there is no ψ column to hide."""
    text = _text('#live-load-table(rows: ((zone: [Nord], storey: [EG], use: [Büro], category: "B"),))', "defaults")
    for word in ("Teilbereich", "Geschoss", "Nutzung", "Kategorie", "[kN/m2]", "[kN]"):
        assert word in text, (word, text)
    assert "ψ" not in text and "psi" not in text, text
    text = _text(LIVE_TABLE, "hidden-zone")
    assert "Teilbereich" not in text, text


def test_a_number_written_over_is_printed_in_orange_and_said_so():
    body = """#live-load-table(columns: ((id: "use", title: [Nutzung]), (id: "category"), (id: "q_k"), (id: "Q_k")),
  rows: ((use: [Archiv], category: "E", q_k: 7.5, Q_k: 7), (use: [Büro], category: "B", q_k: auto, Q_k: auto)))"""
    text = _text(body, "override")
    assert "Archiv E 7.5 7" in text, text
    assert "In Orange" in text, text
    assert ORANGE in _svg(body, "override-svg")
    plain = _svg(LIVE_TABLE, "plain-svg")
    assert ORANGE not in plain, "a table with no value written over prints no orange"
    assert "In Orange" not in _text(LIVE_TABLE, "plain-text")


def test_category_e_is_refused_at_auto_naming_the_clause():
    message = _refusal('#live-load-table(rows: ((use: [Lager], category: "E"),))', "category-e")
    assert message.startswith("live-load-table: row 1") and "E" in message and "8.2.2" in message, message


def test_an_unknown_category_is_refused_listing_the_valid_ones():
    message = _refusal('#live-load-table(rows: ((category: "Z"),))', "category-z")
    assert message.startswith("live-load-table: row 1") and "valid categories" in message and "A1" in message, message
    message = _refusal('#live-load-table(rows: ((category: [B]),))', "category-content")
    assert "as a string" in message, message


def test_a_row_without_a_category_leaves_its_values_empty():
    text = _text('#live-load-table(columns: ((id: "use", title: [Nutzung]), (id: "category"), (id: "q_k")), rows: ((use: [Flur]),))', "no-category")
    assert "Flur" in text, text


def test_no_live_load_instance_of_the_export_carries_a_psi():
    """The ψ vars left `calc/domains/live_load.py` (and the frozen export of the example project): a category carries its load and nothing else."""
    for category in ("A1", "B", "E", "H"):
        assert not [k for k in _live(category) if k.startswith("psi")], category


def test_a_psi_column_is_no_known_column_and_a_planted_psi_var_is_printed_by_nothing():
    """`psi_0` has no heading of its own any more: the column is refused like any column of an unknown id that has no title. And an export written before the ψ vars went, carrying them still, makes no table print them."""
    message = _refusal('#live-load-table(columns: ((id: "use"), (id: "psi_0")), rows: ((use: [Büro]),))', "psi-column")
    assert message.startswith('live-load-table: column "psi_0" has no title') and "psi_0" in message, message
    root, data = _root("psi")
    calc = json.loads((data / "calculations.json").read_text(encoding="utf-8"))
    vars_b = calc["domains"]["live-load"]["instances"]["B"]["vars"]
    for key, value in (("psi_0", 0.7), ("psi_1", 0.5), ("psi_2", 0.3)):
        vars_b[key] = {"value": value, "unit": "", "symbol": key, "label": "Reduktionsbeiwert", "level": 3,
                       "source": "norm:SIA 260:2013, Tabelle 2", "norm": "SIA 260", "norm_ref": "Tabelle 2"}
    (data / "calculations.json").write_text(json.dumps(calc, ensure_ascii=False), encoding="utf-8")
    body = '#live-load-table(hidden: ("zone", "storey"), rows: ((use: [Büro], category: "B"),))\n#show-bibliography(data: false)'
    text = _text(body, "psi-planted", root=root)
    assert f"Büro B {_num(vars_b['q_k']['value'])} {_num(vars_b['Q_k']['value'])}" in text, text
    assert "ψ" not in text and "0.7 0.5" not in text, text
    assert "SIA 260" not in text, "SIA 260 is not a source of the table any more"


def test_the_headings_follow_the_reports_language():
    text = _text('#live-load-table(rows: ((zone: [N], storey: [RDC], use: [Bureau], category: "B", q_k: 4),))', "french", lang="fr")
    for word in ("Zone", "Niveau", "Utilisation", "Catégorie", "En orange"):
        assert word in text, (word, text)


# --- dead-load-table --------------------------------------------------------------------------

def test_the_load_column_takes_a_value_of_the_export():
    """The cell Woodcore's Variables tab writes, `[#val("…", domain: …, type: "val", level: 1)]`, is printed as the export's own value."""
    var = conftest.exported("calculations.json")["domains"]["dead-load"]["instances"]["EL+AL-Dach mit Wasser"]["vars"]["gk_ak_gew"]
    body = """#dead-load-table(rows: (
  (zone: [Wohnen], storey: [OG], buildup: [Bodenaufbau], load: 1.5),
  (zone: [Dach], storey: [Dach], buildup: [Dachaufbau], load: [#val("gk_ak_gew", domain: ("dead-load", "EL+AL-Dach mit Wasser"), type: "val", level: 1)]),
))"""
    text = _text(body, "dead")
    assert "Auflast" in text and "[kN/m2]" in text, text
    assert "Wohnen OG Bodenaufbau 1.5" in text, text
    assert f"Dach Dach Dachaufbau {_num(var['value'])}" in text, text
    french = _text('#dead-load-table(rows: ((load: 1),))', "dead-fr", lang="fr")
    assert "Poids propre non-structural" in french, "an Auflast is SIA 261's «poids propre non-structural»"


def test_auto_has_nothing_to_fill_from_in_a_load_column():
    message = _refusal('#dead-load-table(rows: ((load: auto),))', "dead-auto")
    assert message.startswith("dead-load-table: row 1, column \"load\"") and "auto" in message, message


# --- doc-field, doc-checklist, doc-choice ------------------------------------------------------

def test_a_field_prints_its_label_its_value_or_the_placeholder():
    text = _text('#doc-field(label: [Nutzungsdauer], value: 50, unit: "Jahre")\n#doc-field(label: [Bauherrschaft])\n'
                 '#doc-field(label: [Schnee], value: [#val("q_k11", domain: ("snow-load", "SL"), level: 1)])', "field")
    q = conftest.exported("calculations.json")["domains"]["snow-load"]["instances"]["SL"]["vars"]["q_k11"]
    assert "Nutzungsdauer: 50 Jahre" in text and "Bauherrschaft: [...]" in text, text
    assert f"Schnee: {_num(q['value'])} kN/m2" in text, text


def test_a_checklist_prints_what_is_ticked_and_explains_it():
    """What was chosen and nothing else, as a list (the engineer's rule of 06.10.2026: a report does not show the options left aside) -- each ticked option with its paragraph --; every option with its box where `only-checked: false` asks for them; «[…]» where nothing is ticked yet."""
    options = """options: (
    (id: "a", label: [Baugrundrisiko], checked: true, text: [Ein akzeptiertes Risiko.]),
    (id: "b", label: [Vandalismus], checked: false, text: [Nicht gedruckt.]),
    (id: "c", label: [Hochwasser], checked: true),
  )"""
    text = _text(f"#doc-checklist(label: [Risiken], {options})", "checklist")
    assert "Risiken" in text and "Baugrundrisiko" in text and "Hochwasser" in text and "Ein akzeptiertes Risiko." in text, text
    assert "Vandalismus" not in text and "Nicht gedruckt." not in text and "✔" not in text, text
    every = _text(f"#doc-checklist(label: [Risiken], {options}, only-checked: false)", "checklist-every")
    assert "✔ Baugrundrisiko" in every and "✔ Hochwasser" in every and "Vandalismus" in every and every.count("✔") == 2, every
    assert "Ein akzeptiertes Risiko." in every and "Nicht gedruckt." not in every, every
    none = _text('#doc-checklist(label: [Risiken], options: ((id: "b", label: [Vandalismus], checked: false),))', "checklist-none")
    assert "Risiken" in none and "[...]" in none and "Vandalismus" not in none, none


def test_a_choice_prints_its_answer_and_refuses_two():
    options = '((id: "i", label: [BWK I]), (id: "ii", label: [BWK II]), (id: "iii", label: [BWK III]))'
    # the answer alone after its label, by default (06.10.2026): the zone a building stands in, and not the four it does not
    text = _text(f'#doc-choice(label: [Bauwerksklasse], options: {options}, selected: "ii")', "choice")
    assert "Bauwerksklasse: BWK II" in text and "BWK III" not in text, text
    text = _text(f'#doc-choice(label: [Bauwerksklasse], options: {options})', "choice-none")
    assert "Bauwerksklasse: [...]" in text, text
    text = _text(f'#doc-choice(label: [Klasse], options: {options}, other: [BWK IV nach Sondernorm])', "choice-other")
    assert "Klasse: BWK IV nach Sondernorm" in text and "BWK III" not in text, text
    every = _text(f'#doc-choice(label: [Bauwerksklasse], options: {options}, selected: "ii", only-selected: false)', "choice-every")
    assert all(f"BWK {n}" in every for n in ("I", "II", "III")), every
    every = _text(f'#doc-choice(label: [Klasse], options: {options}, other: [BWK IV nach Sondernorm], only-selected: false)', "choice-other-every")
    assert "Andere: BWK IV nach Sondernorm" in every, every
    message = _refusal(f'#doc-choice(options: {options}, selected: "iv")', "choice-unknown")
    assert message.startswith("doc-choice: selected:") and '"iii"' in message, message
    message = _refusal(f'#doc-choice(options: {options}, selected: "i", other: [x])', "choice-two")
    assert message.startswith("doc-choice: selected: and other: both answer"), message


# --- doc-image, doc-plan -----------------------------------------------------------------------

def test_a_picture_or_the_frame_standing_in_its_place():
    root, _data = _root("image")
    pictures = sorted(p.name for p in (root / "Images").glob("*.png"))
    if not pictures:
        raise Skip("the example project carries no picture")
    text = _text(f'#doc-image(caption: [Profil])\n#doc-image(file: "Images/{pictures[0]}", caption: [Bild], width: 40%)\n'
                 f'#doc-image(file: "/Images/{pictures[0]}")', "image", root=root)
    assert "[Abbildung]" in text and "Abbildung 1: Profil" in text and "Abbildung 2: Bild" in text, text
    text = _text('#doc-image(placeholder: [Auszug aus dem geotechnischen Bericht])', "image-placeholder", lang="fr", root=root)
    assert "Auszug aus dem geotechnischen Bericht" in text, text
    assert "[Figure]" in _text("#doc-image()", "image-fr", lang="fr", root=root)


def test_a_plan_extract_or_the_frame_standing_in_its_place():
    plans = conftest.exported("plans.json")["plans"]
    if not plans:
        raise Skip("the example project carries no position plan")
    plan = sorted(plans)[0]
    text = _text(f'#doc-plan(plan: none, caption: [Belastungsplan])\n#doc-plan(plan: "{plan}", width: 60%)', "plan")
    assert "[Auszug aus dem Positionsplan]" in text and "Belastungsplan" in text, text
    assert f"Positionsplan {plan}" in text, text


def test_an_excerpt_of_an_annex_or_the_frame_standing_in_its_place():
    """`doc-extract` is `show-extract` with a frame while no excerpt is chosen (v0.115): the example project's excerpt prints as a numbered figure with the caption the call gives, an unchosen one a frame in the report's language."""
    excerpts = conftest.exported("annexes.json")["excerpts"]
    if not excerpts:
        raise Skip("the example project carries no excerpt")
    excerpt = sorted(excerpts)[0]
    text = _text(f'#doc-extract(excerpt: none, caption: [Schnittkräfte])\n#doc-extract(excerpt: "{excerpt}", width: 60%, caption: [Biegemomente])', "extract")
    assert "[Auszug aus einem Anhang]" in text and "Schnittkräfte" in text and "Biegemomente" in text, text
    assert "[Extrait d’une annexe]" in _text("#doc-extract()", "extract-fr", lang="fr")


def test_the_annexes_object_prints_the_annex_pages_of_the_excerpts_the_document_shows():
    """`doc-annexes` is `show-annexes`: the pages of a source come only from the excerpts THIS document shows, so a document that shows none prints no annex page, and `heading:` is the level of the annex's name."""
    excerpts = conftest.exported("annexes.json")["excerpts"]
    if not excerpts:
        raise Skip("the example project carries no excerpt")
    excerpt = sorted(excerpts)[0]
    shown = _text(f'#show-extract("{excerpt}")\n#doc-annexes(heading: 3)', "annexes-shown")
    assert "Anhang A" in shown, shown
    not_shown = _text('#doc-annexes(heading: 3)', "annexes-not-shown")
    assert "Anhang A" not in not_shown, not_shown


# --- doc-signatures, show-norm-list -------------------------------------------------------------

def test_the_signatures_print_a_row_per_signatory_under_its_group():
    body = """#doc-signatures(rows: (
  (group: [Bauherrschaft], role: [Vertretung], name: [A. Beispiel], place: [Bern], date: [1.10.2026]),
  (group: [Projektverfassende], role: [Architekt:in]),
  (group: [Projektverfassende], role: [Ingenieur:in]),
))"""
    text = _text(body, "signatures")
    for word in ("Funktion", "Name", "Ort, Datum", "Unterschrift", "Bauherrschaft", "Projektverfassende",
                 "Vertretung A. Beispiel Bern, 1.10.2026", "Architekt:in", "Ingenieur:in"):
        assert word in text, (word, text)
    assert text.count("Projektverfassende") == 1, "one group line for the two rows that share it"
    text = _text('#doc-signatures(rows: ((role: [Bauherrschaft]),), place-date: false)', "signatures-no-date")
    assert "Ort, Datum" not in text and "Unterschrift" in text, text
    assert "Signature" in _text('#doc-signatures(rows: ((role: [Maître de l\'ouvrage]),))', "signatures-fr", lang="fr")


def test_the_norms_a_section_names_are_listed_in_full_and_registered():
    norms = json.loads((ROOT / "calc" / "norms" / "norms.json").read_text(encoding="utf-8"))["references"]
    sia260 = next(e for e in norms if e["key"] == "SIA 260")
    body = ('#show-norm-list(keys: ("SIA 260:2013", "SIA 999 (unbekannt)", [Eine Zeile von Hand], "SIA 260"))\n'
            "Weiter.\n#show-bibliography(data: false)")
    text = _text(body, "norms")
    head, tail = text.split("Weiter.")
    assert sia260["title"]["de"] in head and head.count(sia260["designation"]) == 1, head   # an alias, listed once
    assert "SIA 999 (unbekannt)" in head and "Eine Zeile von Hand" in head, head
    assert tail.count(sia260["designation"]) == 1 and "SIA 999 (unbekannt)" in tail, "the keys are registered for the bibliography, a document and its alias once"
    assert "Eine Zeile von Hand" not in tail, "content is registered nowhere"
    # an empty selection prints nothing between the two words -- the page's own number comes after them
    assert _text("Vorher\n#show-norm-list()\nNachher", "norms-empty").split()[:3] == ["Vorher", "Nachher", "1"]


# --- refusals -----------------------------------------------------------------------------------

REFUSED = (
    ('#doc-table(columns: "part")', "doc-table: columns: is an array"),
    ('#doc-table(columns: ((id: "a"),))', "doc-table: column \"a\" has no title:"),
    ('#doc-table(columns: ((id: "a", title: [A], titel: [B]),))', "doc-table: column 1 carries \"titel\""),
    ('#doc-table(columns: ((id: "1a", title: [A]),))', "doc-table: column 1: id:"),
    ('#doc-table(columns: ((id: "a", title: [A]), (id: "a", title: [B])))', "doc-table: two columns are called \"a\""),
    ('#doc-table(columns: ((id: "a", title: [A], kind: "big"),))', "doc-table: column \"a\": kind:"),
    ('#doc-table(columns: ((id: "a", title: [A]),), hidden: "a")', "doc-table: hidden: is an array of column ids -- write (\"a\",)"),
    ('#doc-table(columns: ((id: "a", title: [A]),), hidden: ("b",))', "doc-table: hidden: names \"b\""),
    ('#doc-table(columns: ((id: "a", title: [A]),), rows: ((b: [x]),))', "doc-table: row 1 names the column \"b\""),
    ('#doc-table(columns: ((id: "a", title: [A]),), rows: ((a: true),))', "doc-table: row 1, column \"a\" is [content]"),
    ('#doc-table(columns: ((id: "a", title: [A]),), header: "no")', "doc-table: header: is true or false"),
    ('#live-load-table(columns: ((id: "extra"),))', "live-load-table: column \"extra\" has no title:"),
    ('#doc-field(value: (1, 2))', "doc-field: value: is [content]"),
    ('#doc-checklist(options: ((id: "a", label: [A]), (id: "a", label: [B])))', "doc-checklist: two options are called \"a\""),
    ('#doc-checklist(options: ((id: "a"),))', "doc-checklist: option \"a\" has no label:"),
    ('#doc-checklist(options: ((id: "a", label: [A], checked: "yes"),))', "doc-checklist: option \"a\": checked:"),
    ('#doc-choice(options: ((id: "a", label: [A], checked: true),))', "doc-choice: option 1 carries \"checked\""),
    ('#doc-image(width: "40%")', "doc-image: width: is a length or a ratio"),
    ('#doc-image(file: 12)', "doc-image: file:"),
    ('#doc-plan(plan: 3)', "doc-plan: plan:"),
    ('#doc-fire-plan(plan: 3)', "doc-fire-plan: plan:"),
    ('#doc-fire-plan(width: "40%")', "doc-fire-plan: width: is a length or a ratio"),
    ('#doc-extract(excerpt: 3)', "doc-extract: excerpt:"),
    ('#doc-extract(width: "40%")', "doc-extract: width: is a length or a ratio"),
    ('#doc-annexes(heading: 0)', "doc-annexes: heading:"),
    ('#doc-signatures(rows: ((role: [A], signature: [x]),))', "doc-signatures: row 1 carries \"signature\""),
    ('#show-norm-list(keys: "SIA 260")', "show-norm-list: keys: is an array of the documents to list"),
    ('#show-norm-list(keys: ("",))', "show-norm-list: keys: holds"),
    ('#show-norm-list(project: 1)', "show-norm-list: project:"),
)


def test_every_malformed_argument_is_refused_naming_the_command():
    """A shape the command does not take is refused, the message starting with the command's name and saying what to write: an object its editor cannot read back is one Woodcore would silently rewrite."""
    bad = []
    for i, (body, start) in enumerate(REFUSED):
        message = _refusal(body, f"refused-{i}")
        if not message.startswith(start):
            bad.append(f"{body}\n    expected {start!r}\n    got      {message!r}")
    assert not bad, "refusals that do not say what they should:\n  " + "\n  ".join(bad)


def test_the_complete_and_minimal_calls_print_without_a_word():
    """The two calls the commands tab copies -- every argument at its default, and none -- compile, and print nothing that is not the command's own: a table's empty heading, a frame, «[…]»."""
    sys.path.insert(0, str(ROOT / "calc" / "tools"))
    import build_reference as ref
    records = {r["name"]: r for r in ref.lib_bindings(ROOT)}
    samples = ref.sample_arguments(PROJECT.data_dir)
    calls = []
    for name in COMMANDS:
        calls += [ref.call_complete(records[name], samples), ref.call_minimal(records[name], samples)]
    text = _text("\n".join(calls), "defaults")
    assert "[...]" in text and "[Abbildung]" in text and "[Auszug aus dem Positionsplan]" in text and "[Auszug aus dem Brandschutzplan]" in text, text
