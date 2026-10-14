"""The documents the engine can name in full, out of `calc/norms/norms.json` (docs/architecture/layout.md §11, docs/typst/api-conventions.md §10bis).

One entry per norm or document the engine already cites somewhere -- SIA 260, 261, 261/1, 263, 265, 265/1, SN EN 14592, SZS C5, STE Compact 02, the VKF fire-protection directives, and bauforumstahl's Arbeitshilfe -- each with the four fields a bibliography prints: its **designation**, its **full title**, its **edition** and its **publisher**. The report's `#show-bibliography` reads the same file from Typst (`lib/bibliography.typ`), so the two cannot come to name a norm two ways; this module is what checks it before an export or a test takes anything out of it.

It is a **catalogue, not a list to print**: an entry is set on the page only where the report actually cites it. A norm a report never cites is never printed, and a norm a report cites without an entry is printed as it was cited, under «Weitere Dokumente» -- so a project's own documents (a manufacturer's ETA, an office handbook) need nothing here: they belong in that project's `references.bib`.

⚠️ Every title, edition and publisher is read off the edition's own title page in `ExternalFiles/000-Normes/` (section 2 rule 13) and the entry says which, in its `_source` -- or, for an edition the library does not hold, off the publisher's own page (the SIA shop's preview PDF, the cover of a VKF directive on www.bsvonline.ch), which the `_source` then names by its address and marks «Not in ExternalFiles/000-Normes/». Nothing checks the `_source`'s words, only that it is there: a web address is as good a page to turn to as a file name. ⚠️ No `_source` is ever printed: naming the library's file in the report is what the engineer refused.
"""

import json
from pathlib import Path

import validation

NAME = "norms"
PATH = Path(__file__).resolve().parent / (NAME + ".json")

# Which block of the bibliography an entry belongs to. The third block, for a citation no entry names, is the report's and not a kind an entry may claim: an entry that knows itself is either a norm or a piece of literature.
KINDS = ("norm", "literature")

# The languages a title or a publisher may be given in, where the document gives it in several. A language the entry leaves out falls back on German, then on whichever it has -- a document printed in one language only says its title once (docs/typst/language.md §4bis).
LANGUAGES = ("de", "fr", "en")

# The four fields a bibliography prints, and the shape each takes: a plain string, or one string per language.
TEXT_FIELDS = ("title", "publisher")
PLAIN_FIELDS = ("designation", "edition")

_cache = {}


def _fail(what):
    raise validation.ValidationError("calc/norms/%s.json: %s" % (NAME, what))


def _text(entry, field, where):
    """One of the fields that may be a string or a dictionary of languages, checked and returned as a dictionary."""
    value = entry.get(field)
    if isinstance(value, str):
        if not value.strip():
            _fail("%s: '%s' is empty" % (where, field))
        return {"": value}
    if not isinstance(value, dict) or not value:
        _fail("%s: '%s' is %r -- expected the text, or one text per language" % (where, field, value))
    for lang, text in value.items():
        if lang not in LANGUAGES:
            _fail("%s: '%s' is given in %r -- the languages are %s" % (where, field, lang, ", ".join(LANGUAGES)))
        if not isinstance(text, str) or not text.strip():
            _fail("%s: '%s' in %s is %r -- expected a non-empty string" % (where, field, lang, text))
    return dict(value)


def _read():
    if "data" in _cache:
        return _cache["data"]
    try:
        with PATH.open(encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        _fail("not found at %s -- the documents the engine names live in calc/norms/" % PATH)
    except json.JSONDecodeError as exc:
        _fail("is not valid JSON: %s" % exc)
    entries = data.get("references")
    if not isinstance(entries, list) or not entries:
        _fail("no 'references' list")
    seen, by_key = {}, []
    for entry in entries:
        if not isinstance(entry, dict):
            _fail("an entry is %r -- expected an object" % (entry,))
        key = entry.get("key")
        if not isinstance(key, str) or not key.strip():
            _fail("an entry's 'key' is %r -- it is the string a citation writes ('SIA 261')" % (key,))
        where = "the entry %r" % key
        if entry.get("kind") not in KINDS:
            _fail("%s: 'kind' is %r -- a bibliography's block is %s"
                  % (where, entry.get("kind"), " or ".join(repr(k) for k in KINDS)))
        for field in PLAIN_FIELDS:
            value = entry.get(field)
            if not isinstance(value, str) or not value.strip():
                _fail("%s: '%s' is %r -- expected a non-empty string" % (where, field, value))
        texts = {field: _text(entry, field, where) for field in TEXT_FIELDS}
        # ⚠️ Required, and the rule with teeth: an entry states the edition its four fields were read off, so that a title can be checked against the page it came from (docs/architecture/principles.md §2 rule 13). It is never printed.
        if not isinstance(entry.get("_source"), str) or not entry["_source"].strip():
            _fail("%s: no '_source' -- name the edition its title was read off, in ExternalFiles/000-Normes/, or the publisher's page it was read off where the library lacks it" % where)
        aliases = entry.get("aliases", [])
        if not isinstance(aliases, list) or any(not isinstance(a, str) or not a.strip() for a in aliases):
            _fail("%s: 'aliases' is %r -- expected a list of the other strings a citation may write" % (where, aliases))
        record = dict(entry)
        record.update(texts)
        record["aliases"] = list(aliases)
        for name in [key] + list(aliases):
            if name in seen:
                _fail("%s: %r is also named by the entry %r -- one citation, one entry" % (where, name, seen[name]))
            seen[name] = key
        by_key.append(record)
    _cache["data"] = {"references": by_key, "index": seen}
    return _cache["data"]


def references():
    """Every entry, in the file's own order: {key, aliases, kind, designation, title, edition, publisher, _source}."""
    return [dict(r) for r in _read()["references"]]


def keys():
    """Every string a citation may write to reach an entry -- the keys and their aliases."""
    return sorted(_read()["index"])


def reference(citation):
    """The entry a `norm` field or a `norm:` argument names, by its key or one of its aliases -- `None` where the catalogue has none."""
    index = _read()["index"]
    key = index.get(citation)
    if key is None:
        return None
    for record in _read()["references"]:
        if record["key"] == key:
            return dict(record)
    return None


def text(record, field, lang="de"):
    """One of a record's texts in one language: the language it asks for, else German, else the one the document prints."""
    value = record[field]
    if "" in value:
        return value[""]
    for candidate in (lang, "de"):
        if candidate in value:
            return value[candidate]
    return value[sorted(value)[0]]
