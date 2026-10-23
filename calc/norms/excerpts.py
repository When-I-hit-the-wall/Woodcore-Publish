"""The excerpts of a norm the window shows beside its data: where each is in the edition's PDF, and its words (spec 2026-10-22-onglet-neige-type, ARCH-006, ARCH-013, D-21; docs/architecture/reference-library.md §11bis).

A norm file of calc/norms/ that a calculation tab cites holds two blocks beside its values: `editions` -- per language, the file of the edition shipped in norm-library/ and the pages of the chapter Ctrl+click opens -- and `excerpts` -- per id, its kind (`text`, `figure`) and, per edition, the clause as that edition names it (`ref`: «5.3.4», «Figure 3» / «Figur 3»), its page, its box in PDF points from the page's top-left corner, and its text word for word; an excerpt with `map` opens a site instead of the chapter (Anhang D: 261.sia.ch). The text is copied once, from the edition, and held to it by tests/test_norm_excerpts.py (D-21): a copy that would age without saying so is what that test is for.

**Language**: the window's. An edition the norm file does not list -- English, which SIA 261 has none of -- falls back on German (UI-005, `FALLBACK`). Everything is read through `_loader` (G3) and checked once; a defect stops, naming the file and the excerpt. No Qt: calc/tools/excerpt_image.py renders the box, calc/tools/norm_reader.py opens the chapter.
"""

from dataclasses import dataclass
from pathlib import Path

from norms import _loader, library

HERE = Path(__file__).resolve().parent
FALLBACK = "de"
LANGUAGES = ("de", "fr", "en")
KINDS = ("text", "figure")

_cache = {}


@dataclass(frozen=True)
class Excerpt:
    """One excerpt in one edition: what the bubble shows and where Ctrl+click goes. `lang` is the edition's, which is the asked language's or German's."""
    norm: str            # the norm file's stem (`sia261-2020-5.2-schnee`)
    id: str
    kind: str            # text | figure
    lang: str            # the edition shown
    edition: str         # «SIA 261:2020»
    ref: str             # the clause as that edition names it
    page: int
    box: tuple           # (x0, y0, x1, y1) in PDF points from the top-left corner, or () for the whole page
    text: str
    file: str            # the edition's PDF, in norm-library/
    chapter: tuple       # (first page, last page) of the chapter Ctrl+click opens
    map_url: str = ""    # a site Ctrl+click opens instead (`{lang}` filled)

    def pdf(self):
        """The edition's PDF, or None where it is not there (REQ-004)."""
        return library.pdf(self.file)


def _fail(name, what):
    _loader.fail(name, what)


def _check(name, data):
    editions = data.get("editions")
    if not isinstance(editions, dict):
        _fail(name, "no 'editions' -- the file and the chapter of each edition the excerpts are read off")
    for lang, ed in editions.items():
        if lang.startswith("_"):
            continue
        if lang not in LANGUAGES:
            _fail(name, "editions: %r is no language of %s" % (lang, ", ".join(LANGUAGES)))
        if not isinstance(ed.get("file"), str) or not ed["file"].lower().endswith(".pdf"):
            _fail(name, "editions.%s.file is %r -- the edition's PDF in norm-library/" % (lang, ed.get("file")))
        pages = ed.get("chapter")
        if not (isinstance(pages, list) and len(pages) == 2 and all(isinstance(p, int) and p > 0 for p in pages) and pages[0] <= pages[1]):
            _fail(name, "editions.%s.chapter is %r -- [first page, last page]" % (lang, pages))
    langs = {lang for lang in editions if not lang.startswith("_")}
    if FALLBACK not in langs:
        _fail(name, "editions: no %r edition to fall back on" % FALLBACK)
    excerpts = data.get("excerpts")
    if not isinstance(excerpts, dict):
        _fail(name, "no 'excerpts'")
    for eid, ex in excerpts.items():
        if eid.startswith("_"):
            continue
        where = "excerpts.%s" % eid
        if ex.get("kind") not in KINDS:
            _fail(name, "%s.kind is %r -- %s" % (where, ex.get("kind"), ", ".join(KINDS)))
        eds = ex.get("editions")
        if not isinstance(eds, dict) or set(eds) - langs or FALLBACK not in eds:
            _fail(name, "%s.editions names %r -- the editions are %s, and %r is required" % (where, sorted(eds or ()), ", ".join(sorted(langs)), FALLBACK))
        for lang, ed in eds.items():
            at = "%s.editions.%s" % (where, lang)
            if not isinstance(ed.get("ref"), str) or not ed["ref"].strip():
                _fail(name, "%s.ref is %r -- the clause as the edition names it" % (at, ed.get("ref")))
            if not isinstance(ed.get("page"), int) or ed["page"] < 1:
                _fail(name, "%s.page is %r -- a page of the PDF, from 1" % (at, ed.get("page")))
            box = ed.get("box")
            if box is not None and not (isinstance(box, list) and len(box) == 4 and all(isinstance(v, (int, float)) and 0 <= v <= 2000 for v in box)
                                        and box[0] < box[2] and box[1] < box[3]):
                _fail(name, "%s.box is %r -- [x0, y0, x1, y1] in PDF points from the top-left corner, x0 < x1 and y0 < y1" % (at, box))
            if not isinstance(ed.get("text"), str) or not ed["text"].strip():
                _fail(name, "%s.text is %r -- the excerpt's words, as the edition prints them" % (at, ed.get("text")))
        if "map" in ex:
            url = (ex["map"] or {}).get("url")
            if not isinstance(url, str) or not url.startswith("https://") or "{lang}" not in url:
                _fail(name, "%s.map.url is %r -- an https address with {lang}" % (where, url))
    return data


def read(name):
    """The norm file `name` (its stem), its excerpts checked -- read once."""
    if name not in _cache:
        data = _loader.load(HERE / (name + ".json"))
        _loader.edition(name, data)
        _cache[name] = _check(name, data)
    return _cache[name]


def ids(name):
    """The ids of the excerpts of `name`, in the file's order."""
    return [eid for eid in read(name)["excerpts"] if not eid.startswith("_")]


def edition_of(name, lang):
    """The language of the edition shown for `lang`: its own where the file lists it, else German."""
    editions = read(name)["editions"]
    return lang if lang in editions and not lang.startswith("_") else FALLBACK


def excerpt(name, eid, lang):
    """The excerpt `eid` of `name` in the edition shown for `lang` (`edition_of`): a KeyError where the file has no such excerpt -- what the declaration's test catches."""
    data = read(name)
    ex = data["excerpts"][eid]
    shown = lang if lang in ex["editions"] else FALLBACK
    ed = ex["editions"][shown]
    book = data["editions"][shown]
    url = ""
    if ex.get("map"):
        langs = ex["map"].get("langs") or {}
        url = ex["map"]["url"].replace("{lang}", langs.get(lang, langs.get(FALLBACK, FALLBACK)))
    return Excerpt(norm=name, id=eid, kind=ex["kind"], lang=shown, edition=data["edition"], ref=ed["ref"], page=ed["page"],
                   box=tuple(ed.get("box") or ()), text=ed["text"], file=book["file"], chapter=tuple(book["chapter"]), map_url=url)


def chapter(name, lang):
    """(the PDF's path or None, first page, last page) of the chapter Ctrl+click opens, in the edition shown for `lang`."""
    book = read(name)["editions"][edition_of(name, lang)]
    return library.pdf(book["file"]), book["chapter"][0], book["chapter"][1]
