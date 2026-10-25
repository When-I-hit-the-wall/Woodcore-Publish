"""The excerpts of SIA 261 the snow tab shows (calc/norms/excerpts.py, spec 2026-10-22-onglet-neige-type, ARCH-006, ARCH-013, REQ-004, UI-005, D-21).

What is held here:

* **the file's shape** -- every excerpt checked by its reader, a defect refused naming the excerpt;
* **the copy does not age unseen** (D-21): the text of each excerpt, copied once from the prototype's table `N`, is found word for word in the text layer of the edition shipped in norm-library/ -- on its page, or the next where the clause runs over the page break (5.2.6). What a text layer cannot give is left out of the comparison and said: the symbol font (μ, α, Δ, the subscripts written `_`), the superscripts (m², kN/m³), the equations, whose layout the layer scrambles, and spaces, hyphens and quotes;
* **the box is the clause**: the words of the box's first line are the clause's;
* **German is the fallback** of an edition the file lacks -- English;
* **a missing PDF is no error**: the excerpt keeps its words, `pdf()` says None.
"""

TIER = "fast"  # tests/run_tests.py --fast

import copy
import re

import conftest
from conftest import Skip
from norms import _loader, excerpts, library
import validation

NAME = "sia261-2020-5.2-schnee"
LIBRARY = conftest.norms_library()

# What a text layer loses or scrambles, taken out of both sides before they are compared (see the module's docstring)
_DROP = re.compile(r"[\s_μαΔΣγηƥƩ·'’\-–−­\x00-\x1f]")   # the control bytes are the symbol font's glyphs a layer cannot name (Δ comes out as \x04); SIA 265/1's layer writes γ and η as ƥ and Ʃ
_SUPER = str.maketrans({"²": "2", "³": "3", "ψ": ""})
_GLYPH = re.compile(r"/g[0-9a-f]")   # SIA 260:2013's layer names its Greek glyphs by their number (γ /g9, ψ /g8 in the French edition): dropped as the letters are (issue #113)


def _norm(text):
    return _DROP.sub("", _GLYPH.sub("", text.translate(_SUPER)))


def _layer(pdf, page):
    from pypdf import PdfReader
    pages = PdfReader(str(pdf)).pages
    return "".join(_norm(pages[n - 1].extract_text()) for n in (page, page + 1) if n <= len(pages))


def _prose(text):
    """The parts of an excerpt's text a text layer prints in reading order: its lines that are no equation, cut at their brackets."""
    for line in text.split("\n"):
        if "=" in line or "≤" in line or " · " in line:   # an equation (a check's too: SIA 265 (14)), or a row of a figure's values (Anhang D's corrections, which the layer prints in the map's order)
            continue
        for part in re.split(r"[()]", line):
            if len(_norm(part)) >= 15:
                yield part


def test_every_excerpt_is_read_and_checked():
    ids = excerpts.ids(NAME)
    assert {"5.1.4", "5.2.6", "5.3.4", "5.3.7", "fig2", "fig3", "fig4", "fig5", "annexD"} <= set(ids)
    for eid in ids:
        for lang in ("fr", "de", "en"):
            e = excerpts.excerpt(NAME, eid, lang)
            assert e.kind in excerpts.KINDS and e.text.strip() and e.page > 0, (eid, lang)
            assert e.edition == "SIA 261:2020"
            assert e.chapter == ((26, 29) if e.lang == "fr" else (25, 28)), (eid, lang, e.chapter)


def test_english_falls_back_on_german_and_french_is_its_own():
    assert excerpts.excerpt(NAME, "5.3.4", "en").lang == "de"
    assert excerpts.excerpt(NAME, "5.3.4", "fr").lang == "fr"
    assert excerpts.excerpt(NAME, "fig3", "fr").ref == "Figure 3" and excerpts.excerpt(NAME, "fig3", "de").ref == "Figur 3"
    assert excerpts.edition_of(NAME, "en") == "de"


def test_the_map_of_annex_d_is_read_in_the_windows_language():
    assert excerpts.excerpt(NAME, "annexD", "fr").map_url == "https://261.sia.ch/?lang=fr&layer=snow"
    assert excerpts.excerpt(NAME, "annexD", "de").map_url == "https://261.sia.ch/?lang=de&layer=snow"
    assert excerpts.excerpt(NAME, "annexD", "en").map_url == "https://261.sia.ch/?lang=de&layer=snow"
    assert excerpts.excerpt(NAME, "5.3.4", "fr").map_url == ""


def test_a_defect_is_refused_naming_the_excerpt():
    good = _loader.load(excerpts.HERE / (NAME + ".json"))
    for path, value, said in ((("excerpts", "5.3.4", "kind"), "table", "excerpts.5.3.4.kind"),
                              (("excerpts", "5.3.4", "editions", "fr", "box"), [548, 10, 40, 20], "excerpts.5.3.4.editions.fr.box"),
                              (("excerpts", "5.3.4", "editions", "fr", "text"), " ", "excerpts.5.3.4.editions.fr.text"),
                              (("editions", "de", "chapter"), [28, 25], "editions.de.chapter"),
                              (("excerpts", "annexD", "map", "url"), "http://261.sia.ch/", "excerpts.annexD.map.url")):
        data = copy.deepcopy(good)
        node = data
        for key in path[:-1]:
            node = node[key]
        node[path[-1]] = value
        try:
            excerpts._check(NAME, data)
        except validation.ValidationError as exc:
            assert said in str(exc) and NAME in str(exc), (path, str(exc))
        else:
            raise AssertionError("%s = %r was accepted" % (".".join(path), value))


def test_the_copied_text_is_the_editions_word_for_word():
    """D-21: the copy is held to the PDF shipped with Woodcore -- every prose part of every excerpt, in French and German, is in its page's text layer (or the next page's)."""
    _held_to_the_pdf(NAME)


def _held_to_the_pdf(name):
    if not (LIBRARY / "SIA261-2020-FR.pdf").is_file():
        raise Skip("SIA261-2020-FR.pdf is not in %s -- the norms are shipped in norm-library/" % LIBRARY)
    layers, missing = {}, []
    for eid in excerpts.ids(name):
        for lang in ("fr", "de"):
            e = excerpts.excerpt(name, eid, lang)
            key = (e.file, e.page)
            if key not in layers:
                layers[key] = _layer(LIBRARY / e.file, e.page)
            for part in _prose(e.text):
                if _norm(part) not in layers[key]:
                    missing.append("%s %s p. %d: %r" % (eid, lang, e.page, part))
    assert not missing, "not in the edition's text layer:\n" + "\n".join(missing)


def test_a_text_excerpts_box_holds_its_clause():
    """The box is placed on the clause: the text inside it starts with the clause's words (its number, then its first words)."""
    _boxes_hold_their_clause(NAME)


def _boxes_hold_their_clause(name, kinds=("text",)):
    if not (LIBRARY / "SIA261-2020-FR.pdf").is_file():
        raise Skip("SIA261-2020-FR.pdf is not in %s" % LIBRARY)
    from pypdf import PdfReader
    readers = {}
    for eid in excerpts.ids(name):
        for lang in ("fr", "de"):
            e = excerpts.excerpt(name, eid, lang)
            if e.kind not in kinds or not e.box or e.chapter == (81, 114):   # a table of Annexe C: its box the table, its caption beside it -- its words held by the test above
                continue
            reader = readers.setdefault(e.file, PdfReader(str(LIBRARY / e.file)))
            page = reader.pages[e.page - 1]
            height = float(page.mediabox.height)
            x0, y0, x1, y1 = e.box
            parts = []

            def keep(text, cm, tm, _font, _size):
                x, y = tm[4] * cm[0] + cm[4], tm[5] * cm[3] + cm[5]
                if x0 - 2 <= x <= x1 + 2 and y0 <= height - y <= y1 + 2:   # a line's baseline inside the box
                    parts.append(text)
            page.extract_text(visitor_text=keep)
            inside = _norm("".join(parts))
            prose = next(_prose(e.text), None)
            if prose is None:
                # a table's title that is its proportions alone (h : b : d = 0,5 : 2 : 1): the box holds its reference
                assert _norm(e.ref) in inside, (eid, lang, inside[:60])
                continue
            first = _norm(prose)[:25]
            assert _norm(e.ref) in inside[:40] or first in inside[:40], (eid, lang, inside[:60])   # the box may catch the foot of the equation above it (5.2.3 under (9))
            assert first in inside, (eid, lang, first, inside[:120])


def test_a_missing_pdf_leaves_the_words(monkeypatch=None):
    """REQ-004: an edition not shipped is no error -- its excerpt keeps its words and says it has no PDF."""
    import os
    was = os.environ.get(library.ENV)
    os.environ[library.ENV] = str(conftest.ROOT / ".no-norm-library")
    try:
        e = excerpts.excerpt(NAME, "5.3.4", "fr")
        assert e.pdf() is None and e.text.startswith("Si un glissement")
        assert excerpts.chapter(NAME, "fr") == (None, 26, 29)
    finally:
        if was is None:
            os.environ.pop(library.ENV, None)
        else:
            os.environ[library.ENV] = was


# --- the wind's excerpts (spec 2026-10-23-onglet-vent-briques, V4: REQ-011, REQ-012, ARCH-012)

WIND = "sia261-2020-wind-excerpts"


def test_the_winds_excerpts_cover_chapter_6_annex_e_and_each_building_twice():
    """REQ-011, REQ-012: chapter 6's clauses, Annexe E with 261.sia.ch's wind map, and each of the 37 buildings twice -- its table (the bubble) and its figure alone (the figure printed at level 3) --, in French and in German, English reading German; an excerpt of Annexe C opens its annex at Ctrl+click, every other chapter 6."""
    from norms import sia261_wind
    ids = set(excerpts.ids(WIND))
    assert {"6.2.1.1", "6.2.1.2", "tab4", "6.2.1.3", "6.2.2.1", "6.2.2.3", "6.2.3.2", "6.3.3", "6.3.5", "fig9", "fig22", "annexE"} <= ids
    for number in sia261_wind.NUMBERS:
        assert {"tab" + number, "fig" + number} <= ids, number
        for lang, ref in (("fr", "Tableau "), ("de", "Tabelle "), ("en", "Tabelle ")):
            e = excerpts.excerpt(WIND, "fig" + number, lang)
            assert e.kind == "figure" and e.ref.startswith(ref) and e.chapter == (81, 114) and e.box, (number, lang)
    assert excerpts.excerpt(WIND, "6.3.5", "fr").chapter == (30, 35) and excerpts.excerpt(WIND, "6.3.5", "de").chapter == (29, 34)
    assert excerpts.excerpt(WIND, "annexE", "fr").map_url == "https://261.sia.ch/?lang=fr&layer=wind"
    assert excerpts.excerpt(WIND, "annexE", "en").map_url == "https://261.sia.ch/?lang=de&layer=wind"


def test_the_winds_copied_text_is_the_editions_word_for_word():
    """D-21: every prose part of the wind's excerpts, in French and German, is in its page's text layer."""
    _held_to_the_pdf(WIND)


def test_the_winds_text_boxes_hold_their_clause():
    _boxes_hold_their_clause(WIND)


# --- the materials' excerpts (spec 2026-10-24-onglet-materiaux, UI-008, ARCH-009): each table whole, the source a material shows

MATERIALS = ("sia265-2021-materials-excerpts", "sia261-2020-materials-excerpts", "sia265-1-2018-materials-excerpts")


def test_the_materials_excerpts_cover_every_table_a_material_cites():
    """UI-008: SIA 265 Tabellen 8 and 9, SIA 261 Tabellen 28 to 30, SIA 265/1 Tableaux 6, 9 and 11 to 23 -- each a figure with its box."""
    assert set(excerpts.ids("sia265-2021-materials-excerpts")) == {"tab08", "tab09"}
    assert set(excerpts.ids("sia261-2020-materials-excerpts")) == {"tab28", "tab29", "tab30"}
    assert set(excerpts.ids("sia265-1-2018-materials-excerpts")) == {"tab06", "tab09"} | {"tab%d" % n for n in range(11, 24)}
    for name in MATERIALS:
        for eid in excerpts.ids(name):
            for lang in ("fr", "de", "en"):
                e = excerpts.excerpt(name, eid, lang)
                assert e.kind == "figure" and len(e.box) == 4, (name, eid, lang)


def test_a_norm_of_one_edition_shows_it_in_every_language():
    """ARCH-009: SIA 265/1 is shipped in French alone -- German and English are shown the French edition, not refused for want of a German one."""
    for lang in ("fr", "de", "en"):
        e = excerpts.excerpt("sia265-1-2018-materials-excerpts", "tab19", lang)
        assert e.lang == "fr" and e.page == 42 and e.file == "SIA265-1-2018-FR.pdf"
    assert excerpts.edition_of("sia265-1-2018-materials-excerpts", "de") == "fr"
    assert excerpts.edition_of("sia265-2021-materials-excerpts", "en") == "de"


def test_the_materials_titles_are_the_editions_word_for_word():
    """D-21: each table's title, in each edition, is in its page's text layer."""
    for name in MATERIALS:
        _held_to_the_pdf(name)


def test_the_materials_boxes_hold_their_table():
    """The box of a table starts at its title."""
    for name in MATERIALS:
        _boxes_hold_their_clause(name, kinds=("figure",))


# --- the clauses the «Domaines» tab cites (issue #113, REQ-014, ARCH-014) -------------------------------

DOMAINS = ("sia260-2013-domains-excerpts", "sia261-2020-domains-excerpts", "sia265-2021-domains-excerpts")
CITED = (("SIA 260", "Tableau 1"), ("SIA 260", "4.4.3.4"), ("SIA 261", "2.1"), ("SIA 261", "5.2.2"),
         ("SIA 265", "3.3.2.1"), ("SIA 265", "4.2.3.1"), ("SIA 265", "Tableau 4"), ("SIA 265", "Tableau 8"))


def test_the_eight_clauses_of_the_domains_find_their_excerpt_and_others_none():
    """ARCH-014: each clause the prototype's domains cite finds one excerpt, by the clause as the edition names it (French or German); a clause no file lists has none and raises nothing; two excerpts of one clause give none."""
    for norm, section in CITED:
        for lang in ("fr", "de", "en"):
            e = excerpts.for_citation(norm, section, lang)
            assert e is not None and e.edition.startswith(norm + ":"), (norm, section, lang)
    assert excerpts.for_citation("SIA 265", "Tabelle 8", "de").ref == "Tabelle 8"
    assert excerpts.for_citation("SIA 265", "9.9.9", "fr") is None and excerpts.for_citation("SIA 999", "1", "fr") is None
    assert excerpts.for_citation("", "", "fr") is None
    names = excerpts._with_excerpts()
    try:
        excerpts._cache["_with"] = names + ["sia265-2021-materials-excerpts"]
        assert excerpts.for_citation("SIA 265", "Tableau 8", "fr") is None, "two excerpts of one clause gave a bubble"
    finally:
        excerpts._cache["_with"] = names


def test_the_domains_excerpts_are_the_editions_word_for_word_and_their_boxes_hold_them():
    """CON-003: copied off the named editions shipped in norm-library/, their words held to the text layer, each box inside its page and starting at its clause."""
    from pypdf import PdfReader
    for name in DOMAINS:
        for eid in excerpts.ids(name):
            for lang in ("fr", "de"):
                e = excerpts.excerpt(name, eid, lang)
                if e.pdf() is not None:
                    page = PdfReader(str(e.pdf())).pages[e.page - 1]
                    assert e.box[2] <= float(page.mediabox.width) and e.box[3] <= float(page.mediabox.height), (name, eid, lang, e.box)
        _held_to_the_pdf(name)
        _boxes_hold_their_clause(name, kinds=("text", "figure"))


# --- the member checks' clauses and figures (issue #112, UI-012) ---------------------------------------------

CHECKS = ("sia265-2021-checks-excerpts", "sia265-1-2018-checks-excerpts")


def test_the_member_checks_excerpts_are_the_editions_word_for_word_and_their_boxes_hold_them():
    """UI-012: the clauses and figures the four member checks' tabs cite, read off the editions in norm-library/ -- every prose line in the page's text layer, each text box starting at its clause, each figure's box holding its caption."""
    from pypdf import PdfReader
    for name in CHECKS:
        if not all((LIBRARY / ed["file"]).is_file() for ed in _loader.load(excerpts.HERE / (name + ".json"))["editions"].values()):
            raise Skip("an edition of %s is not in norm-library/" % name)
        _held_to_the_pdf_any(name)
        _boxes_hold_their_clause(name, kinds=("text",))
        for eid in excerpts.ids(name):
            for lang in ("fr", "de"):
                e = excerpts.excerpt(name, eid, lang)
                page = PdfReader(str(e.pdf())).pages[e.page - 1]
                assert e.box[2] <= float(page.mediabox.width) and e.box[3] <= float(page.mediabox.height), (name, eid, lang, e.box)
                if e.kind == "figure":
                    height = float(page.mediabox.height)
                    found = []

                    def keep(text, cm, tm, _font, _size, e=e, found=found, height=height):
                        if text.strip() and _norm(text)[:8] and _norm(e.ref) in _norm(text):
                            found.append(height - (tm[5] * cm[3] + cm[5]))
                    page.extract_text(visitor_text=keep)
                    assert any(e.box[1] <= y <= e.box[3] for y in found), (eid, lang, found, e.box)


def _held_to_the_pdf_any(name):
    layers, missing = {}, []
    for eid in excerpts.ids(name):
        for lang in ("fr", "de"):
            e = excerpts.excerpt(name, eid, lang)
            key = (e.file, e.page)
            if key not in layers:
                layers[key] = _layer(LIBRARY / e.file, e.page)
            for part in _prose(e.text):
                if _norm(part) not in layers[key]:
                    missing.append("%s %s p. %d: %r" % (eid, lang, e.page, part))
    assert not missing, "not in the edition's text layer:\n" + "\n".join(missing)


def test_every_clause_a_member_check_cites_has_its_excerpt():
    """UI-012: each clause a row of `member_check.compute` cites, for every kind of the four tabs and a panel, finds its one excerpt (norms.excerpts.for_citation) -- a panel's table by its material's excerpt."""
    import sys
    sys.path.insert(0, str(conftest.ROOT / "tests"))
    import re as _re
    import test_member_check as tmc
    from domains import member_check as mc, member_check_material as mm, materials_catalogue
    records = [r for r in conftest.exported(mc.EXPORT_FILE)["checks"].values() if not r.get("fire")]
    records += [r for r in tmc._synthetic() if isinstance(r, dict)]
    for kind, extra in (("shear", {"variant": "shear-off", "F": {"value": 5, "unit": "kN"}, "l": 200}), ("shear", {"variant": "shear-perp", "sigma_90": -1.0})):
        src = mc.new_source("X", kind)
        src.update(extra, section={"type": "rec", "b": 100, "h": 200}, moisture_class=1, grade="C24")
        records.append(mc.resolve(src, {}))
    panel = mc.new_source("P", "bending")
    panel.update(section={"type": "rec", "b": 1000, "h": 18}, moisture_class=2, material="sia265-1:osb3", loading={"mode": "plaque", "direction": "par"}, M_y={"value": 0.4, "unit": "kNm"})
    records.append(mc.resolve(mc.stamp_version(panel), {}))
    missing = set()
    for record in records:
        result = mc.compute(record)
        if not result:
            continue
        cited = {("SIA 265", result["clause"])}
        for row in result["rows"]:
            if row.get("clause"):
                cited.add((row.get("norm") or "SIA 265", row["clause"]))
            if row.get("table"):
                cited.add(("SIA 265", row["table"]["clause"]))
        for norm, clause in cited:
            clause = _re.sub(r"\s*\(\d+\)$", "", clause)
            if norm == "SIA 265/1" and clause.startswith("Tableau ") and clause.endswith("b"):
                store, eid = materials_catalogue.find(record["material"]["id"])["excerpt"]
                assert excerpts.excerpt(store, eid, "fr").ref.endswith(clause.split()[-1]), clause
                continue
            if excerpts.for_citation(norm, clause, "fr") is None:
                missing.add((norm, clause))
    assert not missing, sorted(missing)
