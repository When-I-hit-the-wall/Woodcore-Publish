"""The report engine's own words, in the three languages a report can be written in, out of `strings.json` beside this file (docs/typst/language.md §4bis).

`i18n/` is to the engine's words what `norms/` is to the norm's values: the one place they are written down. The file is read by Python -- here, for the text a figure carries, which has to be drawn to be measured -- and by Typst (`lib/i18n.typ`), for everything the report prints. A word said on both sides, such as the note under a connection's figure that Python sizes and Typst fills in, is therefore written once.

What is *not* in it: the engineer's own data. Excel descriptions and text values, sheet names, positions, material names, Woodcore's interface, the prose of `Sections/*.typ`. The glossary is exactly the list of what counts as the engine's words, which is what lets `tl` in Typst translate a label and leave a material alone.

Three blocks, and the middle one is the reason `data/calculations.json` did not have to change at all:

* **`engine`** -- what Typst prints itself, by a key.
* **`templates`** -- a sentence with a hole in it (a sheet's name, a chosen value, a figure's number). It cannot be keyed by its own text, so Typst matches the German by the literal segments around the holes and puts the captured data back into the target language.
* **`terms`** -- the German the export already carries, keyed by itself, the way gettext keys by its source string.

The file is hand-written, so it is checked here before anything is built from it: a language missing from an entry, an empty string, a template whose holes differ between two languages. A glossary that contradicts itself must stop the export naming the key, exactly as a defective norm table does.
"""

import json
import re
from pathlib import Path

STRINGS_FILE = Path(__file__).resolve().parent / "strings.json"

# The languages a report can be written in, in the order the file lists them. The first is the source language: it is the key of the `terms` block, and the text the export itself carries.
LANGUAGES = ("de", "fr", "en")
SOURCE_LANGUAGE = LANGUAGES[0]

# The blocks of the file that carry one entry per key, each entry giving all three languages.
KEYED_BLOCKS = ("engine", "templates")

_HOLE = re.compile(r"\{(\w+)\}")

_cache = None


def _fail(what):
    # validation is imported here rather than at the top, and only when something is wrong:
    # validation.py reads this module's LANGUAGES, so a top-level import either way would be a cycle.
    import validation

    raise validation.ValidationError(f"{STRINGS_FILE.name}: {what}")


def _load():
    """The whole glossary, read once and checked once."""
    global _cache
    if _cache is not None:
        return _cache
    try:
        with STRINGS_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        _fail(f"not found at {STRINGS_FILE} -- the engine's words in three languages live there")
    except json.JSONDecodeError as exc:
        _fail(f"is not valid JSON: {exc}")
    _check(data)
    _cache = data
    return _cache


def _check(data):
    """Every rule the file must satisfy, checked before a word is taken out of it."""
    languages = data.get("languages")
    if languages != list(LANGUAGES):
        _fail(f"languages is {languages!r} -- expected {list(LANGUAGES)!r}")

    for block in KEYED_BLOCKS:
        entries = data.get(block)
        if not isinstance(entries, dict) or not entries:
            _fail(f"{block} is missing or empty")
        for key, entry in entries.items():
            if not isinstance(entry, dict):
                _fail(f"{block}.{key} is not an object")
            for lang in LANGUAGES:
                if lang not in entry:
                    _fail(f"{block}.{key} has no {lang} -- a key missing from one language would only"
                          f" show the day a report is written in it")
                if not isinstance(entry[lang], str) or not entry[lang].strip():
                    _fail(f"{block}.{key}.{lang} is empty")

    # A template's holes are its contract with the code that fills them: the same names, in any order, in all three languages. A hole missing from the French would silently drop a sheet's name.
    for key, entry in data["templates"].items():
        holes = {lang: sorted(_HOLE.findall(entry[lang])) for lang in LANGUAGES}
        reference = holes[SOURCE_LANGUAGE]
        for lang in LANGUAGES:
            if holes[lang] != reference:
                _fail(f"templates.{key}: {lang} has the holes {holes[lang]} but {SOURCE_LANGUAGE}"
                      f" has {reference}")

        # `translate` names the holes that carry a norm's word -- a choice of SIA 261, not a sheet's name -- and so go through the terms when the sentence is translated (audit 260916)
        listed = entry.get("translate", [])
        if not isinstance(listed, list) or any(name not in reference for name in listed):
            _fail(f"templates.{key}: translate names {listed!r} -- it must list holes of the template, {reference}")

    terms = data.get("terms")
    if not isinstance(terms, dict) or not terms:
        _fail("terms is missing or empty")
    for source, entry in terms.items():
        if not source.strip():
            _fail("terms carries an empty German string as a key")
        if not isinstance(entry, dict):
            _fail(f"terms[{source!r}] is not an object")
        if SOURCE_LANGUAGE in entry:
            _fail(f"terms[{source!r}] carries a {SOURCE_LANGUAGE} of its own -- the German is the key")
        for lang in LANGUAGES[1:]:
            if lang not in entry:
                _fail(f"terms[{source!r}] has no {lang}")
            if not isinstance(entry[lang], str) or not entry[lang].strip():
                _fail(f"terms[{source!r}].{lang} is empty")


def check():
    """Read and check the glossary, for a caller that only wants to know it is sound."""
    _load()


def language(lang):
    """`lang` if the glossary speaks it, else a blocking error naming the ones it does."""
    if lang not in LANGUAGES:
        _fail(f"no language {lang!r} -- valid languages: {', '.join(LANGUAGES)}")
    return lang


def text(key, lang=SOURCE_LANGUAGE):
    """One word of the `engine` block, in `lang`."""
    entries = _load()["engine"]
    if key not in entries:
        _fail(f"no engine string {key!r} -- valid keys: {', '.join(sorted(entries))}")
    return entries[key][language(lang)]


def template(key, lang=SOURCE_LANGUAGE, **args):
    """One sentence of the `templates` block, in `lang`, with its holes filled in."""
    entries = _load()["templates"]
    if key not in entries:
        _fail(f"no template {key!r} -- valid keys: {', '.join(sorted(entries))}")
    pattern = entries[key][language(lang)]
    holes = set(_HOLE.findall(pattern))
    missing = holes - set(args)
    if missing:
        _fail(f"templates.{key}: nothing given for {', '.join(sorted(missing))}")
    return _HOLE.sub(lambda m: str(args[m.group(1)]), pattern)


def term(source, lang=SOURCE_LANGUAGE):
    """`source` -- the German the export carries -- in `lang`, or unchanged when the glossary does not have it.

    Unchanged rather than refused, deliberately: this is what a material's name, an Excel description or a value the engineer typed goes through, and none of them is the engine's word to translate.
    """
    if lang == SOURCE_LANGUAGE:
        return source
    entry = _load()["terms"].get(source)
    return entry[language(lang)] if entry else source


def terms():
    """The whole German-keyed dictionary, for a caller that checks coverage."""
    return dict(_load()["terms"])


def segments(pattern):
    """A template's literal parts, in order -- what lies between its holes. `"Element {n}"` gives `["Element ", ""]`.

    The same split `lib/i18n.typ` does, and the reason neither side needs a regular expression: a string matches the template when it starts with the first segment, ends with the last, and carries the others in order, whatever the data in between.
    """
    return _HOLE.split(pattern)[::2]


def match(source_text):
    """The template `source_text` was composed from, as `(key, {hole: text})`, or None.

    The German the export carries is matched, never the translation, so this asks only the source language. The captures are keyed by the hole's *name*, not by its position, so a language that puts the sheet's name before the list where the German puts it after still comes out right. A string that matches two templates takes the first in the file's order, which is why a template's literal part should say enough to be recognised.
    """
    for key, entry in _load()["templates"].items():
        parts = segments(entry[SOURCE_LANGUAGE])
        if len(parts) < 2:
            continue  # a template with no hole is a term, not a pattern
        if not source_text.startswith(parts[0]) or not source_text.endswith(parts[-1]):
            continue
        rest, captures, ok = source_text[len(parts[0]):], [], True
        for part in parts[1:-1]:
            cut = rest.find(part)
            if cut < 0 or not part:
                ok = False
                break
            captures.append(rest[:cut])
            rest = rest[cut + len(part):]
        if not ok:
            continue
        tail = parts[-1]
        if len(rest) < len(tail):
            continue
        captures.append(rest[:len(rest) - len(tail)] if tail else rest)
        names = _HOLE.findall(entry[SOURCE_LANGUAGE])
        if all(captures) and len(captures) == len(names):
            return key, dict(zip(names, captures))
    return None


def translate(source_text, lang=SOURCE_LANGUAGE):
    """`source_text` in `lang`: a term if the glossary has it, else the template it was composed from, else unchanged.

    The same three steps, in the same order, as `tl` in lib/i18n.typ.
    """
    if lang == SOURCE_LANGUAGE:
        return source_text
    entry = _load()["terms"].get(source_text)
    if entry:
        return entry[language(lang)]
    found = match(source_text)
    if found is None:
        return source_text
    key, captures = found
    for name in _load()["templates"][key].get("translate", []):
        captures[name] = term(captures[name], lang)
    return template(key, lang, **captures)
