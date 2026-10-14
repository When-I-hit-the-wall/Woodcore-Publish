"""A text the engineer places on a drawing, written once for the four drawing engines -- the schemas, the static models, the position plans and the fire-protection plans (issue #43, spec docs/requirements/completed/2026-10-11-variables-liees-champs-et-textes.md, REQ-010, REQ-011, ARCH-003).

What a text holds, whatever engine draws it, beside the place that engine gives it in its own coordinates (`at`, D-13):

    "text": "N = {1}\\nb = {2}",
    "vars": {"1": {"domain": "snow-load", "instance": "SL", "var": "F", "show": "symbol",
                   "last": {"value": 18.75, "unit": "kN", "symbol": "F"}},
             "2": {"domain": "wind-load", "instance": "WL", "var": "b", "show": "value"}}

- `text` is what is printed, a line per line of it; `{1}` is a **token**, where the variable `vars["1"]` is printed. A literal brace is written twice, `{{` and `}}`. A token naming no variable, and a brace standing alone, are defects of the file Woodcore wrote: the export stops naming the file and the field (D-13, `CLAUDE.md`).
- a variable of `vars` is a link (`links.check_link`: `domain`, `instance`, `var`, `factor`, `offset`, `origin`) and two keys of its own: `show`, «value» -- `18.75 kN` -- or «symbol» -- `F = 18.75 kN` -- chosen per insertion (D-09); `last`, what the variable gave when the window last saved (`refresh`, D-14), printed where it can no longer be read, with a warning (D-06).

Any variable of the export may be inserted, with no unit to match (D-08): a text prints a value, it fills no field. The value is printed as a figure prints a number (`figure_number`: at most three decimals, the real minus), in the variable's own unit after its factor and offset; the symbol as the window shows it, through `typst_math.to_figure`, so that a figure's text cuts its subscripts as the window sets them.

The text is set by `svg_text.draw`, the one text engine of the figures (D-19): an underscore in what the engineer types makes a subscript, as it does in every label of the static models and the schemas.

Nothing here reads a file and nothing imports Qt: the window and the export call the same functions with the values they hold, so a text shows on screen what the report will print (ARCH-007).
"""

import re

import engine
import typst_math
from domains import links, svg_text
from domains.statics_geometry import figure_number

# The collection a drawing's texts are held in, in each of the four sources; and what a new one is called (T1, T2, ...).
COLLECTION = "texts"
PREFIX = "T"

# How a variable is printed (D-09): its value and unit, or its symbol, an equals sign and its value and unit.
SHOWS = ("value", "symbol")
DEFAULT_SHOW = "value"

# The keys a text's variable carries besides its link's.
VAR_EXTRAS = ("show", "last")

# `{{`, `}}`, a token `{1}`, or a brace standing alone -- the last a defect.
_TOKEN = re.compile(r"\{\{|\}\}|\{([A-Za-z0-9_]+)\}|[{}]")


# --- the token text ----------------------------------------------------------------

def pieces(text):
    """`text` cut into what is printed as it is and the tokens between: [("text", "N = "), ("var", "1")]. A brace standing alone raises ValueError naming where it is."""
    out, i = [], 0
    for m in _TOKEN.finditer(text):
        if m.start() > i:
            out.append(("text", text[i:m.start()]))
        found = m.group(0)
        if found in ("{{", "}}"):
            out.append(("text", found[0]))
        elif m.group(1) is not None:
            out.append(("var", m.group(1)))
        else:
            raise ValueError(f"a brace stands alone at character {m.start() + 1} -- a literal brace is written twice, {{{{ or }}}}")
        i = m.end()
    if i < len(text):
        out.append(("text", text[i:]))
    merged = []
    for kind, value in out:
        if merged and kind == "text" and merged[-1][0] == "text":
            merged[-1] = ("text", merged[-1][1] + value)
        else:
            merged.append((kind, value))
    return merged


def tokens(text):
    """The tokens `text` names, in the order it names them, each once."""
    try:
        return list(dict.fromkeys(value for kind, value in pieces(text) if kind == "var"))
    except ValueError:
        return []


def escape(text):
    """What the engineer types, written into a token text: each brace doubled, so a brace typed is printed and never read as a token."""
    return str(text).replace("{", "{{").replace("}", "}}")


def next_token(entry):
    """The first free token of a text: "1", then "2" -- the name `insert` gives a variable."""
    taken = set((entry.get("vars") or {})) | set(tokens(entry.get("text") or ""))
    n = 1
    while str(n) in taken:
        n += 1
    return str(n)


def insert(entry, link, at=None, show=DEFAULT_SHOW):
    """Inserts a variable into a text, at character `at` of its text (its end where None), and returns its token -- what the pane's «Insérer une variable» does with the choice the «Variables» tab hands back."""
    key = next_token(entry)
    var = dict(link)
    var["show"] = show if show in SHOWS else DEFAULT_SHOW
    entry.setdefault("vars", {})[key] = var
    text = entry.get("text") or ""
    at = len(text) if at is None else max(0, min(int(at), len(text)))
    entry["text"] = text[:at] + "{" + key + "}" + text[at:]
    return key


def remove_var(entry, key):
    """Takes a variable out of a text, its token with it."""
    (entry.get("vars") or {}).pop(key, None)
    entry["text"] = (entry.get("text") or "").replace("{" + key + "}", "")
    if not entry.get("vars"):
        entry.pop("vars", None)


def drop_unused(entry):
    """The variables of `vars` no token names any longer, taken off -- what the window does before it saves, so the file holds no variable nothing prints."""
    named = set(tokens(entry.get("text") or ""))
    found = entry.get("vars") or {}
    for key in [k for k in found if k not in named]:
        del found[key]
    if "vars" in entry and not found:
        del entry["vars"]
    return entry


def link_of(var):
    """A text's variable as the link it is: its own keys taken off."""
    return {key: value for key, value in var.items() if key not in VAR_EXTRAS}


# --- what a file may say -----------------------------------------------------------

def check(entry, fail, what):
    """One text's own fields: its `text` a string whose every token names a variable of `vars`, and every variable of `vars` a link with a `show` and, where it has one, a `last` (D-13). `fail(message)` is called on the first breach, naming `what` -- a defect of a file Woodcore wrote."""
    text = entry.get("text")
    if not isinstance(text, str):
        fail(f"{what}'s text must be a string, got {text!r}")
    try:
        found = pieces(text)
    except ValueError as exc:
        fail(f"{what}'s text {text!r}: {exc}")
        return
    variables = entry.get("vars", {})
    if not isinstance(variables, dict):
        fail(f"{what}'s vars must be an object, got {variables!r}")
    for kind, key in found:
        if kind == "var" and key not in variables:
            fail(f"{what}'s text names {{{key}}}, which no variable of its vars is -- each token names one, and a literal brace is written twice")
    for key, var in variables.items():
        where = f"{what}'s variable {{{key}}}"
        if not isinstance(var, dict):
            fail(f"{where} must be an object naming a variable of the export, got {var!r}")
        show = var.get("show", DEFAULT_SHOW)
        if show not in SHOWS:
            fail(f"{where}'s show is {show!r} -- {' or '.join(SHOWS)}")
        last = var.get("last")
        if last is not None and (not isinstance(last, dict) or not isinstance(last.get("unit", ""), str) or not isinstance(last.get("symbol", ""), str)):
            fail(f"{where}'s last must be {{value, unit, symbol}}, got {last!r}")
        links.check_link(link_of(var), fail, where)


def is_linked(source, collection=COLLECTION):
    """Whether any text of a source names a variable -- what a source's version follows, as its other links do."""
    return any((entry.get("vars") or {}) for entry in source.get(collection) or [] if isinstance(entry, dict))


# --- what a text prints ---------------------------------------------------------------

def _value_text(value, unit):
    number = figure_number(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else str(value)
    return f"{number} {unit}".strip() if unit else number


def resolve_var(var, values):
    """What one variable of a text gives now: {text, value, unit, symbol, stale, missing}. Where it cannot be read, its `last`, and `stale` with the reason (D-06); where it has no last either, `?`, which is what a figure prints for a value it could not read (the static models' rule)."""
    link = link_of(var)
    last = var.get("last") or {}
    found = links.resolve(link, values, None, last.get("value"))
    record = links.lookup(link, values) or {}
    if found["stale"]:
        value, unit, symbol = last.get("value"), last.get("unit", ""), last.get("symbol", "")
    else:
        value, unit, symbol = found["value"], found["unit"], record.get("symbol") or ""
    symbol = symbol or link["var"]
    shown = "?" if value is None else _value_text(value, unit)
    if var.get("show", DEFAULT_SHOW) == "symbol":
        shown = f"{typst_math.to_figure(symbol)} = {shown}"
    return {"text": shown, "value": value, "unit": unit, "symbol": symbol, "stale": found["stale"], "missing": found["missing"]}


def resolve(entry, values, where=""):
    """A text as it prints now: (lines, provenance, warnings). `lines` its lines, every token replaced by what its variable gives; `provenance` [{token, variable, value, unit, stale}] for the export's record (REQ-012); `warnings` a note per variable that kept its last value, naming `where`, the token and the variable (D-06)."""
    variables = entry.get("vars") or {}
    out, provenance, notes = [], [], []
    for kind, value in pieces(entry.get("text") or ""):
        if kind == "text":
            out.append(value)
            continue
        found = resolve_var(variables[value], values)
        out.append(found["text"])
        provenance.append({"token": value, "variable": link_of(variables[value]), "value": found["value"], "unit": found["unit"], "stale": found["stale"]})
        if found["stale"]:
            notes.append(engine.Note("text_stale", f"{where}: the text's {{{value}}} prints its last value -- {found['missing']}",
                                     where=where, field="{" + value + "}", detail=found["missing"]))
    return "".join(out).split("\n"), provenance, notes


def lines(entry, values):
    """A text's lines as they print now -- `resolve` without its record."""
    return resolve(entry, values)[0]


def refresh(entry, values):
    """Writes into each variable of a text the `last` it gives now -- what the window does before it saves (D-14). A variable that cannot be read keeps the last it has."""
    for var in (entry.get("vars") or {}).values():
        found = resolve_var(var, values)
        if not found["stale"]:
            var["last"] = {"value": links._clean(found["value"]), "unit": found["unit"], "symbol": found["symbol"]}
    return entry


def refresh_all(source, values, collection=COLLECTION):
    """`refresh` for every text of a source."""
    for entry in source.get(collection) or []:
        drop_unused(entry)
        refresh(entry, values)
    return source


# --- how a text is drawn ---------------------------------------------------------------

def icon_svg(ink):
    """The Text tool's button symbol, the same in the four engines: a T, drawn as strokes so that no font is asked for, in `ink`."""
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
            f'<path d="M4.5 7.5 V4.5 H19.5 V7.5 M12 4.5 V19.5 M8.5 19.5 H15.5" fill="none" stroke="{ink}" stroke-width="2.2" stroke-linejoin="round"/></svg>')


# The space between two lines of a text, as a share of its size: the static models' labels' own.
LINE_SPACING = 1.25


def box(text_lines, size):
    """The half-width and half-height of a text of these lines at `size`, from the one table of widths (`svg_text.text_width`)."""
    width = max((svg_text.text_width(line, size) for line in text_lines), default=0.0)
    return max(width, size) / 2.0, max(len(text_lines), 1) * LINE_SPACING * size / 2.0


def draw(out, at, text_lines, size, colour, halo=None, rotate=None):
    """A text's lines, centred on `at`, stacked down from the first, each set by `svg_text.draw` -- the one place a drawing's text is drawn, for the four engines (ARCH-003). `halo` draws each line first in white, that wide, so the text reads over what it lies on."""
    top = at[1] - (len(text_lines) - 1) / 2.0 * LINE_SPACING * size
    for i, line in enumerate(text_lines):
        if line.strip():
            svg_text.draw(out, (at[0], top + i * LINE_SPACING * size), line, size, colour, "middle", False, rotate, halo)
