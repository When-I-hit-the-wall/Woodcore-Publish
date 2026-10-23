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
_DROP = re.compile(r"[\s_μαΔΣ·'’\-–−­\x00-\x1f]")   # the control bytes are the symbol font's glyphs a layer cannot name (Δ comes out as \x04)
_SUPER = str.maketrans({"²": "2", "³": "3"})


def _norm(text):
    return _DROP.sub("", text.translate(_SUPER))


def _layer(pdf, page):
    from pypdf import PdfReader
    pages = PdfReader(str(pdf)).pages
    return "".join(_norm(pages[n - 1].extract_text()) for n in (page, page + 1) if n <= len(pages))


def _prose(text):
    """The parts of an excerpt's text a text layer prints in reading order: its lines that are no equation, cut at their brackets."""
    for line in text.split("\n"):
        if "=" in line or " · " in line:   # an equation, or a row of a figure's values (Anhang D's corrections, which the layer prints in the map's order)
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
    if not (LIBRARY / "SIA261-2020-FR.pdf").is_file():
        raise Skip("SIA261-2020-FR.pdf is not in %s -- the norms are shipped in norm-library/" % LIBRARY)
    layers, missing = {}, []
    for eid in excerpts.ids(NAME):
        for lang in ("fr", "de"):
            e = excerpts.excerpt(NAME, eid, lang)
            key = (e.file, e.page)
            if key not in layers:
                layers[key] = _layer(LIBRARY / e.file, e.page)
            for part in _prose(e.text):
                if _norm(part) not in layers[key]:
                    missing.append("%s %s p. %d: %r" % (eid, lang, e.page, part))
    assert not missing, "not in the edition's text layer:\n" + "\n".join(missing)


def test_a_text_excerpts_box_holds_its_clause():
    """The box is placed on the clause: the text inside it starts with the clause's words (its number, then its first words)."""
    if not (LIBRARY / "SIA261-2020-FR.pdf").is_file():
        raise Skip("SIA261-2020-FR.pdf is not in %s" % LIBRARY)
    from pypdf import PdfReader
    readers = {}
    for eid in excerpts.ids(NAME):
        for lang in ("fr", "de"):
            e = excerpts.excerpt(NAME, eid, lang)
            if e.kind != "text" or not e.box:
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
            first = _norm(next(_prose(e.text)))[:25]
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
