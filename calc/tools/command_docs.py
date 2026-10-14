"""The French and German of the commands' documentation, as Woodcore's commands tab shows it (docs/typst/command-docs.md §10sexies, v0.86).

The documentation of a command is written once, in English, in its `///` block in lib/ -- what Tinymist shows on hover and docs/typst-reference.xlsx lists -- and that stays the source (section 2 rule 1). What this module adds is its translation for the tab, read from `calc/i18n/commands.json` beside the report's own glossary: one entry per command, and in it one **unit** per paragraph and per argument, each carrying the English it translates.

**A unit is matched on its English, not on its position.** That is gettext's arrangement and it is what keeps a translation honest: a paragraph whose English was edited since it was translated no longer matches anything, so the tab shows it in English, marked, rather than showing the old sentence as though it said the new one. tests/test_commands.py fails on it, naming the command and the unit, so an edit to a `///` block is not finished until its translation follows -- the same obligation section 2 rule 14 puts on the examples.

What is never translated: the code between backticks, the names of commands and arguments, the ids, the symbols, the types after `->` (a type is not prose).

**The reference's own words are one file too, `calc/i18n/reference.json`**: the categories' names and the one line that introduces each, and the words the reference says about every command -- «Arguments», «Appel minimal», «Exemple 1», «Niveau», «Défini dans» -- read by the website and, since v0.94, by Woodcore's commands tab, whose STRINGS carry no copy of them any more. So the site and the window cannot come to name one category two ways.

**Which levels an example is shown at is decided here, once** (`example_levels`): Woodcore's 1 · 2 · 3 selector, the committed pages build_examples.py renders and the website's level buttons all read it. So are a command page's signature, its arguments' rows and the calls it offers (`signature`, `arguments`, `calls`, v0.94), which Woodcore's commands tab reads and the website's command page sets the same way.

Nothing here imports Qt, so the test reads exactly what the tab reads.
"""

import json
import re
from pathlib import Path

import build_reference as ref  # the /// blocks' own reading: the signature's parameters
import command_preview as preview  # the levels a page is rendered at, and what pins one

ROOT = Path(__file__).resolve().parent.parent.parent  # the program: calc/i18n/ is its own
PATH = ROOT / "calc" / "i18n" / "commands.json"
REFERENCE_PATH = ROOT / "calc" / "i18n" / "reference.json"
SCHEMA_VERSION = "1.0"
LANGUAGES = ("fr", "de")  # English is the /// blocks themselves
REFERENCE_LANGUAGES = ("fr", "de", "en")  # the reference's own words are written in all three: they are nobody's source

# A code span, as Markdown writes one: between single backticks, or between double ones where the code itself holds a backtick -- `` `M / a` ``, a raw block. Read with single backticks alone, a double span followed by more code in the same paragraph took the words between them for code (v0.87, eq's `formula`).
CODE_SPAN = re.compile(r"``.+?``|`[^`]+`")

# How a paragraph is read to be set (v0.89, from commands_tab.py): its code spans first, then **bold** and *italic*. Here rather than in the tab so that the website's build (website/build.py), which runs where there is no Qt, sets the same paragraph the same way the window does.
PROSE_CODE_SPAN = re.compile(r"(``.+?``|`[^`]+`)")
BOLD = re.compile(r"\*\*(.+?)\*\*")
# An asterisk opens an emphasis only after a space or a bracket and closes one only before a space or punctuation: `F*_x,i`, the most unfavourable force of a polar moment, carries two asterisks that are not emphasis.
ITALIC = re.compile(r"(?<![\w*])\*(?=\S)([^*]+?)(?<=\S)\*(?![\w*])")


def prose(text, code, words, bold, italic):
    """One paragraph's reading: each code span set by `code` and parked behind a placeholder, the rest by `words`, then the emphasis (`bold`, `italic`: re.sub templates), then the spans put back -- so nothing inside a code span is ever read as emphasis, while an emphasis may still run across one."""
    spans = []

    def park(match):
        span = match.group(1)
        spans.append(code(span[2:-2].strip() if span.startswith("``") else span[1:-1]))
        return f"\x00{len(spans) - 1}\x00"

    parked = PROSE_CODE_SPAN.sub(park, text)
    out = ITALIC.sub(italic, BOLD.sub(bold, words(parked)))
    return re.sub("\x00(\\d+)\x00", lambda m: spans[int(m.group(1))], out)


def load(path=PATH):
    """The translation file, or an empty one where it is missing or unreadable -- the tab then shows the English, which is the documentation itself."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"schema_version": SCHEMA_VERSION, "commands": {}}
    data.setdefault("commands", {})
    return data


def _lookup(units, english, lang):
    """The translation of one English text among a command's units, or None."""
    for unit in units:
        if unit.get("en") == english:
            text = unit.get(lang)
            return text if isinstance(text, str) and text.strip() else None
    return None


def localise(name, block, lang, table=None):
    """A parsed doc block (build_reference.parse_doc_block) with its prose in `lang`, and how many units stayed English.

    Returns (block, untranslated). For "en", or a language this file does not carry, the block is returned as it is. A unit with no translation keeps its English and is counted, so the tab can say so.
    """
    if lang not in LANGUAGES:
        return block, 0
    table = load() if table is None else table
    entry = table.get("commands", {}).get(name) or {}
    paragraphs_units = entry.get("paragraphs") or []
    argument_units = entry.get("arguments") or {}
    missing = 0
    paragraphs = []
    for english in block["paragraphs"]:
        text = _lookup(paragraphs_units, english, lang)
        if text is None:
            missing += 1
            text = english
        paragraphs.append(text)
    bullets = []
    for arg, kind, english in block["bullets"]:
        unit = argument_units.get(arg)
        text = _lookup([unit], english, lang) if isinstance(unit, dict) else None
        if text is None:
            missing += 1
            text = english
        bullets.append((arg, kind, text))
    localised = dict(block)
    localised.update(paragraphs=paragraphs, summary=" ".join(paragraphs), bullets=bullets)
    return localised, missing


def gaps(records, table=None):
    """What the tests hold: for every public command, the units with no current translation, and the units nothing matches any more.

    `records` are lib bindings with their parsed block merged in (the tab's own records). Returns (missing, orphans), each a sorted list of (command, what, detail).
    """
    table = load() if table is None else table
    commands = table.get("commands", {})
    missing, orphans = [], []
    names = set()
    for record in records:
        name = record["name"]
        names.add(name)
        entry = commands.get(name) or {}
        units = entry.get("paragraphs") or []
        args = entry.get("arguments") or {}
        live_paragraphs = set(record["paragraphs"])
        for i, english in enumerate(record["paragraphs"]):
            for lang in LANGUAGES:
                if _lookup(units, english, lang) is None:
                    missing.append((name, f"paragraph {i + 1} ({lang})", english[:80]))
        for unit in units:
            if unit.get("en") not in live_paragraphs:
                orphans.append((name, "paragraph", str(unit.get("en"))[:80]))
        live_args = {}
        for arg, _kind, english in record["bullets"]:
            live_args[arg] = english
            unit = args.get(arg)
            for lang in LANGUAGES:
                if not isinstance(unit, dict) or _lookup([unit], english, lang) is None:
                    missing.append((name, f"argument {arg} ({lang})", english[:80]))
        for arg, unit in args.items():
            if arg not in live_args or (isinstance(unit, dict) and unit.get("en") != live_args[arg]):
                orphans.append((name, f"argument {arg}", str((unit or {}).get("en"))[:80]))
    for name in commands:
        if name not in names:
            orphans.append((name, "command", "no public command of this name"))
    return sorted(set(missing)), sorted(set(orphans))


def code_spans_kept(table=None):
    """Every translated unit whose code between backticks differs from its English's: `[(command, unit, lang, span)]`. A span is code, and code is never translated."""
    table = load() if table is None else table
    bad = []
    for name, entry in table.get("commands", {}).items():
        units = [("paragraph", u) for u in entry.get("paragraphs") or []]
        units += [(f"argument {a}", u) for a, u in (entry.get("arguments") or {}).items()]
        for where, unit in units:
            spans = sorted(CODE_SPAN.findall(unit.get("en") or ""))
            for lang in LANGUAGES:
                if sorted(CODE_SPAN.findall(unit.get(lang) or "")) != spans:
                    bad.append((name, where, lang, " ".join(spans)[:80]))
    return bad


# --- which levels an example is shown at ----------------------------------------------------------------------

def takes_level(record, block):
    """Whether a command takes a `level:` -- declared in its signature, or documented in its /// block (a named argument a command reads out of a sink is documented and not declared)."""
    argued = {name for name, _default in ref.split_params(record.get("params") or "")}
    argued |= {bullet[0] for bullet in block["bullets"]}
    return "level" in argued


def example_levels(record, block, example):
    """The levels one worked example is shown at: all three for a command taking a `level:`, the report's own base level alone for one that does not, and none for a ```typ-dry fence, which is never compiled.

    An example that writes its own `level:` renders the same page at all three -- a per-call level outranks the report's (docs/typst/report-engine.md §4) -- so it is shown at one: build_examples.py renders it once, the website shows no buttons, and Woodcore shows none either, the rule said in their place (v0.94). The one place this is decided, where the tab, the generator and the site each decided it until now.
    """
    if not example["render"]:
        return ()
    if takes_level(record, block) and preview.fixes_level(example["code"]) is None:
        return tuple(preview.LEVELS)
    return (preview.DEFAULT_LEVEL,)


# --- what a command's page sets, the website's and Woodcore's (v0.94) ----------------------------------------

def signature(record, block):
    """The signature a command's page opens with: `#name(params) -> returns` for a function, the binding itself for a value (`report-level = state(…)`) -- what website/build.py's page_command sets, and Woodcore's commands tab with it."""
    text = f"#{record['name']}({record.get('params') or ''})" if record.get("kind") == "function" else record["signature"]
    returns = block.get("returns")
    return f"{text} -> {returns}" if returns else text


def arguments(record, block):
    """A command's arguments as its page lists them, one row each in the order of its /// block: `name`, the `types` its bullet names, the signature's `default` -- None where the argument is required --, whether it is a `variadic` positional tail (`..values`), and the `text` saying what it does, in the block's language."""
    defaults = dict(ref.split_params(record.get("params") or ""))
    return [{"name": name, "types": [kind.strip() for kind in re.split(r"[,|]", kinds) if kind.strip()], "default": defaults.get(name),
             "variadic": name.startswith(".."), "text": text.strip()} for name, kinds, text in block["bullets"]]


def calls(record, samples):
    """The calls a command's page offers to copy, as (reference.json's word, call), in the website's order: the minimal one, then the complete one where it says more -- none for a binding that is neither a function nor one build_reference.WRITTEN_CALLS writes out. `samples` fill the calls with the export's own ids (build_reference.sample_arguments)."""
    if record.get("kind") != "function" and record["name"] not in ref.WRITTEN_CALLS:
        return []
    minimal, complete = ref.call_minimal(record, samples), ref.call_complete(record, samples)
    return [("call_minimal", minimal)] + ([("call_complete", complete)] if complete != minimal else [])


# --- the reference's own words --------------------------------------------------------------------------------

_REFERENCE = {}


def reference(path=REFERENCE_PATH):
    """calc/i18n/reference.json, read once: `categories` (each one's `label` and, for a category of commands, its `lead`) and `words`, every entry in the three languages."""
    path = Path(path)
    if path not in _REFERENCE:
        _REFERENCE[path] = json.loads(path.read_text(encoding="utf-8"))
    return _REFERENCE[path]


def _text(entry, lang, where):
    text = (entry or {}).get(lang)
    if not isinstance(text, str) or not text.strip():
        raise KeyError(f"calc/i18n/reference.json: no {lang} for {where}")
    return text


def category_label(key, lang, table=None):
    """The name of a category of build_reference.CATEGORIES -- «Calculer dans le rapport» -- in `lang`."""
    table = reference() if table is None else table
    return _text(table["categories"].get(key, {}).get("label"), lang, f"the category {key!r}")


def category_lead(key, lang, table=None):
    """The one line that says what a category's commands are for, in `lang`."""
    table = reference() if table is None else table
    return _text(table["categories"].get(key, {}).get("lead"), lang, f"the lead of the category {key!r}")


def word(key, lang, table=None, **values):
    """One of the reference's words -- «Arguments», «Exemple {n}» -- in `lang`, its holes filled."""
    table = reference() if table is None else table
    text = _text(table["words"].get(key), lang, f"the word {key!r}")
    return text.format(**values) if values else text
