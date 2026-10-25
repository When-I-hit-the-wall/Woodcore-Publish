"""The condensed pages of the Typst commands: calc/i18n/command-pages.json, read, validated and held to lib/ (spec 2026-10-24-onglet-commandes-pages, REQ-001, REQ-003, REQ-006, REQ-013; docs/typst/command-docs.md §10sexies).

**Two texts speak of a command, each for its own reader (D-10).** The `///` block of lib/ is the long reference -- what Tinymist shows on hover and docs/typst-reference.xlsx lists -- and it is the source of the signature, the order of the arguments, their defaults and their types. calc/i18n/command-pages.json is what Woodcore's commands tab and the website show: a one-sentence lead, three or four key points, and for each argument its group, its status, its own sentence, two or three examples and, where it takes a fixed list of values, every value with what it does and the call that shows it -- written by hand in French, German and English, never derived from the block (REQ-013). Neither is a copy of the other, so nothing here translates one into the other: what is held is that they **name the same things** (`disagreements`) -- an argument renamed in lib/ and not in the JSON, a fine value added to lib/display-presets.json and given no sentence, fail tests/test_command_pages.py by name. Prose cannot be held that way; it is a matter of reading the page.

**A malformed file stops** (docs/architecture/principles.md): `load` raises PagesError naming the file and the field -- the schema's walker for the shape, then the three languages of every text and the set every shared value names. The window shows that message where the page would be rather than failing.

Nothing here imports Qt: the tab, the website's build and the tests read the same functions.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT / "calc") not in sys.path:
    sys.path.insert(0, str(ROOT / "calc"))   # validation.py, the schemas' walker

import build_reference as ref  # noqa: E402  -- the /// blocks and the signatures
import validation  # noqa: E402

PATH = ROOT / "calc" / "i18n" / "command-pages.json"
SCHEMA = "command-pages"
SCHEMA_VERSION = "1.0"
LANGS = ("fr", "de", "en")
PRESETS = ROOT / "lib" / "display-presets.json"   # fine-values: the values each fine display argument takes, Typst's and Python's one list

# The groups of a page's arguments, in the order the line of the command and the table set them (UI-003, UI-005). Their names are calc/i18n/reference.json's words `group_<key>`.
GROUPS = ("pos", "show", "text", "cite", "other")

# What no text of a page may hold: the internal references of the /// blocks (D-6, REQ-010), which say nothing to a reader of the reference.
INTERNAL = re.compile(r"\bspec 20|\bspec \w+-\d|\bREQ-\d|\bARCH-\d|\bQ-0\d|\bD-\d|\(v0\.")


# The one fine value a command refuses among fine-values: `#verify` has no `display: "value"` -- its sides are not printed bare -- (lib/formula.typ, check-fine). Read from calc/line_display.py since issue #113, which the «Domaines» tab and «Affichage» offer their values by; tests/test_command_values.py compiles every value a page lists, so a page offering one the engine refuses fails there by name.
from line_display import EXCLUDED  # noqa: E402


class PagesError(ValueError):
    """A command-pages.json that cannot be read as written, naming the file and the field."""


_CACHE = {}


def load(path=PATH):
    """The file, validated: its shape against schemas/command-pages.schema.json, then every text in the three languages and every shared value's set. Raises PagesError naming the file and the field."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PagesError(f"{path.name}: cannot be read -- {exc}") from exc
    except ValueError as exc:
        raise PagesError(f"{path.name}: is not JSON -- {exc}") from exc
    try:
        validation.validate_structure(data, SCHEMA, where=path.name)
    except validation.ValidationError as exc:
        raise PagesError(str(exc)) from exc
    problems = list(_text_problems(data, path.name))
    if problems:
        raise PagesError(problems[0])
    return data


def pages(path=PATH):
    """load(), kept while the file is unchanged."""
    path = Path(path)
    try:
        stamp = path.stat().st_mtime_ns
    except OSError:
        stamp = None
    cached = _CACHE.get(path)
    if cached is None or cached[0] != stamp:
        _CACHE[path] = (stamp, load(path))
    return _CACHE[path][1]


def entry(name, table=None):
    """The page of one command, or None where it has none."""
    table = pages() if table is None else table
    return table["commands"].get(name)


def tr(text, lang):
    """One text in `lang`: a {fr, de, en} object, or a string that holds no words (a call written once for the three languages)."""
    if isinstance(text, str):
        return text
    return text[lang]


def bare(value):
    """A value without the quotes Typst writes it in: `"none"` -> none."""
    return value[1:-1] if len(value) >= 2 and value[0] == value[-1] == '"' else value


def value_text(value, lang, table=None):
    """What one value does, in `lang`: its own text, or its set's in value-texts."""
    text = value["text"]
    if isinstance(text, str):
        table = pages() if table is None else table
        return table["value-texts"][text][bare(value["value"])][lang]
    return text[lang]


def _text_problems(data, file):
    """Every text that misses a language or is empty, and every value naming a set that does not have it."""
    def walk(node, where):
        if isinstance(node, dict):
            if set(LANGS) & set(node) and where.split(".")[-1] not in ("arguments", "commands", "value-texts"):
                for lang in LANGS:
                    text = node.get(lang)
                    if not isinstance(text, str) or not text.strip():
                        yield f"{where}: no {lang} text"
                return
            for key, child in node.items():
                if key == "_comment":
                    continue
                yield from walk(child, f"{where}.{key}")
        elif isinstance(node, list):
            for i, child in enumerate(node):
                yield from walk(child, f"{where}[{i}]")

    yield from walk({k: v for k, v in data.items() if k != "value-texts"}, file)
    for name, values in data["value-texts"].items():
        for value, text in values.items():
            for lang in LANGS:
                if not isinstance(text.get(lang), str) or not text[lang].strip():
                    yield f"{file}.value-texts.{name}.{value}: no {lang} text"
    for command, page in data["commands"].items():
        for arg, spec in page["arguments"].items():
            for i, value in enumerate(spec.get("values") or ()):
                where = f"{file}.commands.{command}.arguments.{arg}.values[{i}]"
                text = value["text"]
                if isinstance(text, str):
                    if bare(value["value"]) not in data["value-texts"].get(text, {}):
                        yield f"{where}.text: the set {text!r} of value-texts has no {bare(value['value'])!r}"
                for part in ("call", "setup"):
                    if isinstance(value.get(part), dict):
                        for lang in LANGS:
                            if not isinstance(value[part].get(lang), str) or not value[part][lang].strip():
                                yield f"{where}.{part}: no {lang} text"


# --- what lib/ says -------------------------------------------------------------------------------------------

def fine_values():
    """lib/display-presets.json's `fine-values`: the values each fine display argument takes, without quotes."""
    return json.loads(PRESETS.read_text(encoding="utf-8"))["fine-values"]


def signature_defaults(record):
    """{argument: its default as the signature writes it, None where it has none}, for a function's record."""
    return dict(ref.split_params(record.get("params") or ""))


def default_of(record, name, spec):
    """An argument's default: the signature's, or the page's own for one read from a sink (`via`), the signature having nothing to say of it."""
    defaults = signature_defaults(record)
    if name in defaults:
        return defaults[name]
    return spec.get("default")


def is_positional(record, name, spec):
    """Whether an argument is written in the line without its name: declared so by the page, or a parameter of the signature with no default and no `..`."""
    if spec.get("positional"):
        return True
    defaults = signature_defaults(record)
    return name in defaults and defaults[name] is None and not name.startswith("..")


def disagreements(records, table=None):
    """Where lib/ and the pages name two different things (REQ-003): for every command that has a page, [(command, what)].

    - an argument of the /// block with no row and no place among the names written by name (`named.members`);
    - a row naming an argument lib/ no longer has -- unless it is read from a sink the block names (`via`, #calc-defaults' `..defaults`);
    - a status the signature contradicts: «optional» for a parameter it requires, «required» for one it gives a default;
    - a fine argument (lib/display-presets.json `fine-values`) whose values are not exactly the engine's, `auto` included where it is the default.
    """
    table = pages() if table is None else table
    fine = fine_values()
    out = []
    for record in records:
        name = record["name"]
        page = table["commands"].get(name)
        if page is None:
            continue
        block = ref.parse_doc_block(record["doc_lines"])
        bullets = [b[0] for b in block["bullets"]]
        args = page["arguments"]
        members = list((page.get("named") or {}).get("members") or ())
        for arg in bullets:
            if arg not in args and arg not in members:
                out.append((name, f"argument {arg!r} of lib/ has no row in command-pages.json"))
        for arg, spec in args.items():
            if arg in bullets:
                pass
            elif spec.get("via") in bullets:
                if "default" not in spec:
                    out.append((name, f"argument {arg!r}, read from {spec['via']}, states no default"))
            else:
                out.append((name, f"argument {arg!r} of command-pages.json is not an argument of lib/ any more"))
            if arg in members:
                out.append((name, f"argument {arg!r} has a row and is among the names written by name"))
        for arg in members:
            if arg not in bullets:
                out.append((name, f"named.members names {arg!r}, which lib/ does not document"))
        defaults = signature_defaults(record)
        for arg, spec in args.items():
            if arg in defaults and not arg.startswith(".."):
                wanted = "required" if defaults[arg] is None else "optional"
                if not spec.get("positional") and spec["status"] != wanted:
                    out.append((name, f"argument {arg!r} is {spec['status']} in command-pages.json, {wanted} in its signature"))
            if arg in fine and spec.get("values"):
                written = [bare(v["value"]) for v in spec["values"]]
                engine = list(fine[arg])
                expected = set(engine) - EXCLUDED.get((name, arg), set()) | ({"auto"} if default_of(record, arg, spec) == "auto" else set())
                if name == "var-table" and arg == "role":
                    expected = set(engine) | {"auto"}
                if set(written) != expected:
                    missing = sorted(expected - set(written))
                    extra = sorted(set(written) - expected)
                    out.append((name, f"argument {arg!r}: values {', '.join(missing) or '-'} of lib/display-presets.json missing, {', '.join(extra) or '-'} unknown to it"))
    return sorted(set(out))


# --- how a call writes a value ----------------------------------------------------------------------------------

def codes(table=None):
    """Every piece of code the pages show, as (command, where, lang, code): the examples, the values, their calls and their set-up lines."""
    table = pages() if table is None else table
    for name, page in table["commands"].items():
        for arg, spec in page["arguments"].items():
            for i, example in enumerate(spec["examples"]):
                for lang in LANGS:
                    yield name, f"{arg}.examples[{i}]", lang, tr(example["code"], lang)
            for i, value in enumerate(spec.get("values") or ()):
                for part in ("call", "setup"):
                    text = value.get(part)
                    if text is None:
                        continue
                    for lang in LANGS:
                        yield name, f"{arg}.values[{i}].{part}", lang, tr(text, lang)


def quoting_errors(table=None):
    """Every fine value written without its quotes (REQ-006): the engine refuses `display: none` (lib/formula.typ written-fine, check-fine) -- a fine value is a string, `"none"` included, `auto` alone bare. [(command, where, code)]."""
    table = pages() if table is None else table
    fine = sorted(fine_values(), key=len, reverse=True)
    pattern = re.compile(r"(?<![\w-])(" + "|".join(re.escape(f) for f in fine) + r")\s*:\s*([^\s,)\]]+)")
    bad = []
    for name, where, _lang, code in codes(table):
        for match in pattern.finditer(code):
            value = match.group(2)
            if value != "auto" and not value.startswith('"'):
                bad.append((name, where, match.group(0)))
    for name, page in table["commands"].items():
        for arg, spec in page["arguments"].items():
            if arg in fine:
                for value in spec.get("values") or ():
                    if value["value"] != "auto" and not value["value"].startswith('"'):
                        bad.append((name, f"{arg}.values", value["value"]))
    return sorted(set(bad))


def internal_references(table=None):
    """Every text that carries an internal reference -- «spec …», «REQ-», «(v0.» (REQ-013, D-6). [(command, where, text)]."""
    table = pages() if table is None else table
    bad = []

    def walk(node, where, command):
        if isinstance(node, str):
            if INTERNAL.search(node):
                bad.append((command, where, node[:80]))
        elif isinstance(node, dict):
            for key, child in node.items():
                walk(child, f"{where}.{key}", command)
        elif isinstance(node, list):
            for i, child in enumerate(node):
                walk(child, f"{where}[{i}]", command)

    for name, page in table["commands"].items():
        walk(page, name, name)
    walk(table["value-texts"], "value-texts", "value-texts")
    return bad


# --- complete --------------------------------------------------------------------------------------------------

def gaps(names, table=None):
    """What a page of each of `names` still lacks (REQ-013): [(command, what)] -- no page at all, a lead, three or four key points, two or three examples an argument, a sentence of its own, and every value of an argument with values given its call."""
    table = pages() if table is None else table
    out = []
    for name in names:
        page = table["commands"].get(name)
        if page is None:
            out.append((name, "no page in command-pages.json"))
            continue
        if not 3 <= len(page["keys"]) <= 4:
            out.append((name, f"{len(page['keys'])} key points, not 3 or 4"))
        for arg, spec in page["arguments"].items():
            if not 2 <= len(spec["examples"]) <= 3:
                out.append((name, f"argument {arg!r}: {len(spec['examples'])} examples, not 2 or 3"))
        for lang in LANGS:
            seen = {}
            for arg, spec in page["arguments"].items():
                text = spec["text"][lang]
                if text in seen:
                    out.append((name, f"arguments {seen[text]!r} and {arg!r} say the same in {lang}"))
                seen.setdefault(text, arg)
    return out
