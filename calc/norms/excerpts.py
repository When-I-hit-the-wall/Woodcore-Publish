"""The excerpts of a norm the window shows beside its data: where each is in the edition's PDF, and its words (spec 2026-10-22-onglet-neige-type, ARCH-006, ARCH-013, D-21; docs/architecture/reference-library.md §11bis).

A norm file of calc/norms/ that a calculation tab cites holds two blocks beside its values: `editions` -- per language, the file of the edition shipped in norm-library/ and the pages of the chapter Ctrl+click opens -- and `excerpts` -- per id, its kind (`text`, `figure`) and, per edition, the clause as that edition names it (`ref`: «5.3.4», «Figure 3» / «Figur 3»), its page, its box in PDF points from the page's top-left corner, and its text word for word; an excerpt with `map` opens a site instead of the chapter (Anhang D: 261.sia.ch). The text is copied once, from the edition, and held to it by tests/test_norm_excerpts.py (D-21): a copy that would age without saying so is what that test is for.

**Language**: the window's. An edition the norm file does not list -- English, which SIA 261 has none of -- falls back on German (UI-005, `FALLBACK`), or on the file's one edition where the norm is shipped in one only -- SIA 265/1, in French (issue #110, ARCH-009). Everything is read through `_loader` (G3) and checked once; a defect stops, naming the file and the excerpt. No Qt: calc/tools/excerpt_image.py renders the box, calc/tools/norm_reader.py opens the chapter.
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
    chapter: tuple       # (first page, last page) of the chapter Ctrl+click opens -- the edition's, or the excerpt's own where it names one (an annex: spec 2026-10-23-onglet-vent-briques, REQ-011)
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
    if FALLBACK not in langs and len(langs) != 1:
        _fail(name, "editions: no %r edition to fall back on -- a norm shipped in several editions needs it" % FALLBACK)
    fallback = _fallback(langs)
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
        if not isinstance(eds, dict) or set(eds) - langs or fallback not in eds:
            _fail(name, "%s.editions names %r -- the editions are %s, and %r is required" % (where, sorted(eds or ()), ", ".join(sorted(langs)), fallback))
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
            own = ed.get("chapter")
            if own is not None and not (isinstance(own, list) and len(own) == 2 and all(isinstance(q, int) and q > 0 for q in own) and own[0] <= ed["page"] <= own[1]):
                _fail(name, "%s.chapter is %r -- [first page, last page] of the part Ctrl+click opens, its page among them" % (at, own))
        if "map" in ex:
            url = (ex["map"] or {}).get("url")
            if not isinstance(url, str) or not url.startswith("https://") or "{lang}" not in url:
                _fail(name, "%s.map.url is %r -- an https address with {lang}" % (where, url))
    return data


def _fallback(langs):
    """The edition shown where the asked one is missing: German, or the norm's one edition."""
    return FALLBACK if FALLBACK in langs or len(langs) != 1 else next(iter(langs))


def _langs(data):
    return {lang for lang in data["editions"] if not lang.startswith("_")}


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
    data = read(name)
    return lang if lang in _langs(data) else _fallback(_langs(data))


def excerpt(name, eid, lang):
    """The excerpt `eid` of `name` in the edition shown for `lang` (`edition_of`): a KeyError where the file has no such excerpt -- what the declaration's test catches."""
    data = read(name)
    ex = data["excerpts"][eid]
    shown = lang if lang in ex["editions"] else _fallback(_langs(data))
    ed = ex["editions"][shown]
    book = data["editions"][shown]
    url = ""
    if ex.get("map"):
        langs = ex["map"].get("langs") or {}
        url = ex["map"]["url"].replace("{lang}", langs.get(lang, langs.get(FALLBACK, FALLBACK)))
    return Excerpt(norm=name, id=eid, kind=ex["kind"], lang=shown, edition=data["edition"], ref=ed["ref"], page=ed["page"],
                   box=tuple(ed.get("box") or ()), text=ed["text"], file=book["file"], chapter=tuple(ed.get("chapter") or book["chapter"]), map_url=url)


def chapter(name, lang):
    """(the PDF's path or None, first page, last page) of the chapter Ctrl+click opens, in the edition shown for `lang`."""
    book = read(name)["editions"][edition_of(name, lang)]
    return library.pdf(book["file"]), book["chapter"][0], book["chapter"][1]


# --- an excerpt found by a citation (issue #113, REQ-014, ARCH-014) ------------------------------------

# The norm files a citation of a domain's line is looked for in (`for_citation`): every file of excerpts, named here so that a file is read by a module (tests/test_norms.py) -- the three of the «Domaines» tab's own clauses (issue #113) and those of the snow, the wind and the materials, which a line may cite as well
CITABLE = ("sia260-2013-domains-excerpts", "sia261-2020-domains-excerpts", "sia265-2021-domains-excerpts", "sia261-2020-5.2-schnee", "sia261-2020-wind-excerpts",
           "sia261-2020-materials-excerpts", "sia265-2021-materials-excerpts", "sia265-1-2018-materials-excerpts",
           "sia265-2021-checks-excerpts", "sia265-1-2018-checks-excerpts")   # the member checks' clauses and figures (issue #112, UI-012)


def _with_excerpts():
    """The stems of the norm files a citation is looked for in (`CITABLE`)."""
    return list(_cache.get("_with") or CITABLE)


def _same_clause(a, b):
    return " ".join(str(a).split()).casefold() == " ".join(str(b).split()).casefold()


def for_citation(norm, section, lang):
    """The excerpt a line of a domain cites -- `norm: "SIA 265"`, `norm-section: "Tableau 8"` -- in the edition shown for `lang`, or None: the one excerpt, among the files of `norm` (their `edition` «SIA 265:2021»), whose clause one of its editions names as `section` («Tableau 8» or «Tabelle 8», «4.2.3.1»). No table beside the files: a clause no file lists, or two files list, has no bubble."""
    if not norm or not section:
        return None
    found = []
    for name in _with_excerpts():
        data = read(name)
        if not str(data.get("edition", "")).startswith(str(norm).strip() + ":"):
            continue
        for eid, ex in data["excerpts"].items():
            if not eid.startswith("_") and any(_same_clause(ed.get("ref", ""), section) for ed in ex["editions"].values()):
                found.append((name, eid))
    return excerpt(found[0][0], found[0][1], lang) if len(found) == 1 else None
