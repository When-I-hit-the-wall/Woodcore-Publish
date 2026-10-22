"""The Typst call each row of the reference workbook offers -- a value written as Typst, then one function per command (call_show_calc, call_val, call_show_plan …) building its call from the export -- split out of calc/build_reference.py (issue #30), moved verbatim. build_reference.py imports every name back.
"""

import functools
import re
from pathlib import Path
from build_reference_lib import (  # split out of this module (issue #30): every name it had is still importable from it
    BULLET_NAME_RE,
    BULLET_RE,
    CATEGORIES,
    DOC_LINE_RE,
    FENCE_RE,
    INTERNAL,
    LET_FN_RE,
    LET_RE,
    LIB_FILES,
    MULTI_BULLET_RE,
    RUNNABLE_FENCE,
    VARIADIC,
    category_of,
    lib_bindings,
    parse_bindings,
    parse_doc_block,
    read_binding,
    read_signature,
    split_params,
    value_signature,
)


# The program (000-Python/): its lib/ is what the catalogue documents. The data it lists the calls of is the project's, handed in by the caller (v0.81).
ROOT = Path(__file__).resolve().parent.parent   # the program: calc/ is its own (calc/tools/ until v0.120, G6)


# Typst globals a var name could shadow if it were bound under its own name: `#let h = ...` would silently replace the spacing function `h()` for the rest of the file.
TYPST_GLOBALS = {"h", "v", "box", "block", "grid", "line", "text", "table", "place", "calc", "sym", "math", "type", "str", "int", "float"}


def typst_str(text):
    """`text` as a Typst string literal: quoted, with backslashes and double quotes escaped."""
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def typst_ident(name):
    """A var name as the Typst identifier a binding gets, the way docs/ writes one (`s_k` -> `s-k`); a name that would shadow a Typst global gets `-var` appended."""
    ident = name.replace("_", "-")
    return ident + "-var" if ident in TYPST_GLOBALS else ident


def _args(*positional, **named):
    """Positional arguments as string literals, then the named ones given (their values already Typst source)."""
    parts = [typst_str(p) for p in positional]
    parts += [f"{key}: {value}" for key, value in named.items() if value is not None]
    return ", ".join(parts)


class Raw(str):
    """Typst source written as it is -- a width (`60%`), `auto`, a `var-of(...)` -- where a plain `str` is a string literal."""


def typst_value(value):
    """A Python value as Typst source: a `Raw` as it is, None as `none`, a bool as `true`/`false`, a number without `.0`, a list or a tuple as an array (one element keeping its comma), anything else as a string literal."""
    if isinstance(value, Raw):
        return str(value)
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return typst_number(value)
    if isinstance(value, (list, tuple)):
        items = [typst_value(item) for item in value]
        return "(" + ", ".join(items) + ("," if len(items) == 1 else "") + ")"
    if isinstance(value, dict):
        # a dictionary: its keys as Typst names where they are (`id`, `strength_class`), as strings where they are not -- `(id: 30mm, type: 20%)`
        if not value:
            return "(:)"
        return "(" + ", ".join((key if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", str(key)) else typst_str(str(key))) + ": " + typst_value(item) for key, item in value.items()) + ")"
    return typst_str(value)


@functools.lru_cache(maxsize=None)
def _signatures():
    return {record["name"]: dict(split_params(record["params"])) for record in lib_bindings(ROOT) if record["kind"] == "function"}


def signature_defaults(name):
    """`{argument: its default as Typst source}` of command `name`, read off its signature in lib/ -- None for a positional one. The one source of every default an option panel starts from and a call leaves out (v0.117, review B02/B03): a default written again in Python would drift from the engine's."""
    try:
        return dict(_signatures()[name])
    except KeyError:
        raise ValueError(f"no command {name!r} in lib/") from None


def _same(a, b):
    return re.sub(r"\s+", "", str(a)) == re.sub(r"\s+", "", str(b))


def call_expression(name, *positional, always=(), **options):
    """`name(...)` with `positional` and the named `options` that differ from the signature's defaults (signature_defaults), in the order given -- an option's Python name with `_` for Typst's `-` (`scale_bar` → `scale-bar`). A named option the command does not take is refused, naming it. `always` names the options written even at their default (show-polar-moment's N, V and M, which say what the call distributes)."""
    defaults = signature_defaults(name)
    parts = [typst_value(value) for value in positional]
    for key, value in options.items():
        arg = key.replace("_", "-")
        if arg not in defaults or arg.startswith(VARIADIC):
            raise ValueError(f"{name} takes no argument {arg!r}")
        text = typst_value(value)
        if defaults[arg] is not None and _same(text, defaults[arg]) and arg not in always:
            continue
        parts.append(f"{arg}: {text}")
    return f"{name}({', '.join(parts)})"


def call_command(name, *positional, always=(), **options):
    """The call of command `name` a section pastes, `#name(...)` -- only what differs from its defaults written out (call_expression). Every `call_*` below goes through it since v0.117, and so does every option panel of Woodcore's «Affichage» views (display_view.py): a call cannot come out two ways."""
    return "#" + call_expression(name, *positional, always=always, **options)


def _given(**options):
    """The options a `call_*` was given: those left at None are the command's own default and not written."""
    return {key: value for key, value in options.items() if value is not None}


_NONE = Raw("none")


def call_var_registry(name, domain, **options):
    """A variable the report itself declared, carried into where the line stands (docs/typst/api-conventions.md §10bis, v0.85).

    `#var("M", domain: "S10 - 0.55 kN Ende")` copies that column's own M into the domain the line stands in,
    which is what carries a result out of the column that computed it so that an `#eq` or a `#verify` below
    can name it. Told from `call_var` by where the value comes from: that one reads a calculation of the
    **export** (`var-of(...)`), this one a `var-domain` of the **report**, which is in no file at all.

    ⚠️ `domain` is required, and that is not a convenience: `#var` reads its value from `domain:` or from a
    positional beside the key, so `#var("R_d")` alone is a call that can never work whatever is declared
    around it -- `var-record` asserts a number. A variable of the report's own default domain has nothing to
    be carried out of and is named by `val` where it stands, so there is no call to offer for it.
    """
    if not domain:
        raise ValueError("call_var_registry: a var-domain is required -- #var(key) alone carries no value")
    return call_command("var", name, domain=domain, **_given(**options))


def call_find(domain=None, type_=None):
    """What there is to name in a call, for one domain (docs/typst/command-docs.md §10sexies, v0.85).

    `#find(object: "variable", domain: "T001")`. `domain` left out is what the report has declared at that
    line, which is what a `#verify` refusing a name is asking about; a pair is a calculation of the export and
    is `call_find_source`'s business, not this one's.
    """
    return call_command("find", object="variable", **_given(domain=domain, type=type_))


def registry_key(name, symbol=None):
    """The name a formula written by hand cites a value by (docs/typst/formulas.md §10quinquies).

    The printed symbol when a formula can spell it -- `a_k`, `q_k11` read better in
    `` `g_k + a_k` `` than the export's own `ak` does -- and the export's name otherwise,
    a key being letters, digits and `_` and never anything else. `#var` keeps the symbol
    the value brought with it either way, so the printed line is unchanged.
    """
    if symbol and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", symbol):
        return symbol
    return name


def typst_number(value):
    """A number as Typst source: no trailing `.0`, no exponent -- `7.5`, `25`, `-6.6`."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"not a number: {value!r}")
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def _by_level(shown):
    """A part of a figure the level decides -- a legend, a scale bar, lengths, centres (spec 2026-10-20-indices-et-niveaux, UI-003): ticked, the command's own `auto`, printed from level 2 and not written; unticked, `false`, left out at every level."""
    return None if shown else False


def _caption(caption):
    """A figure's caption as the calls take it: None or "" the command's own (auto), False `none`, a text that text."""
    if caption is None or caption == "":
        return None
    return _NONE if caption is False else caption


def typst_content(text):
    """`text` as Typst content between `[` and `]`, printed as it is written: the characters markup would read -- a `#`, a bracket, an emphasis, a label, a reference, an equation -- escaped."""
    text = re.sub(r"([\\#\[\]*_`$<>@~])", r"\\\1", str(text))
    # a line that starts like a heading, a list or a term is set apart only there: `= `, `- `, `+ `, `/ `
    return re.sub(r"(?m)^([=\-+/])", r"\\\1", text)


def figure_label(oid):
    """The label a figure of the object `oid` is given -- `fig-vu-skizze` --: the id in lower case, every character a label does not take a `-` (spec 2026-10-15, UI-001)."""
    return "fig-" + (re.sub(r"[^a-z0-9_.:-]+", "-", str(oid).lower()).strip("-") or "x")


@functools.lru_cache(maxsize=1)
def image_vocabulary():
    """The vocabulary of the five image-* commands, lib/image-vocabulary.json's `commands` (spec 2026-10-21-commandes-typst-refonte, ARCH-012): the one table Typst refuses a value with and the calls are written from."""
    import json
    return json.loads((ROOT / "lib" / "image-vocabulary.json").read_text(encoding="utf-8"))["commands"]


def call_image(command, oid, detail_figure=None, detail_legend=None, **options):
    """`image-…("<id>", …)`, the drawing a figure holds, one of the six (ARCH-012; image-polar-moment, spec 2026-10-22-image-polar-moment): `detail_figure` and `detail_legend` lists of the vocabulary's words -- written only where they differ from the command's defaults, a value outside the list refused naming it --, `options` the command's others (`highlight`, `width` as Typst source, `frame`, `zoom`)."""
    entry = image_vocabulary()[command]
    given = {}
    for arg, value in (("detail-figure", detail_figure), ("detail-legend", detail_legend)):
        if value is None:
            continue
        words = [value] if isinstance(value, str) else list(value)
        wrong = [w for w in words if w not in entry[arg]]
        if wrong:
            raise ValueError(f"{command}: {arg} has no {wrong[0]!r} -- valid: {', '.join(entry[arg]) or 'none'}")
        if words != list(entry[arg + "-default"]):
            given[arg.replace("-", "_")] = words[0] if len(words) == 1 else tuple(words)
    for key, value in options.items():
        if value is None:
            continue
        if key not in entry["options"]:
            raise ValueError(f"{command} takes no {key!r} -- it takes {', '.join(entry['options'])}")
        if key == "highlight":
            ids = list(value) if isinstance(value, (list, tuple)) else [value]
            value = tuple(ids) if len(ids) > 1 else ids[0]
        elif key == "width":
            value = Raw(value)
        given[key] = value
    return call_expression(command, oid, **given)


def call_image_figure(command, oid, caption, label=None, **options):
    """The figure a «Copier» button of the five drawings copies, and the one the file of a polar moment writes (ARCH-012, D-13): `#figure(image-…("<id>", …), kind: image, caption: [<caption>]) <label>` -- a native figure that numbers the drawing and is cited by `@label` (`fig-<id>` by default); `options` are `call_image`'s."""
    shown = "" if caption is None else ", caption: [" + typst_content(caption) + "]"   # None: a figure without a caption, numbered all the same
    return "#figure(" + call_image(command, oid, **options) + ", kind: image" + shown + ") <" + (label or figure_label(oid)) + ">"


def figure_of_panel(command, oid, values, caption):
    """The figure a drawing's option panel copies (ARCH-012): the panel's values -- a switch for each thing drawn, a width, the positions or parts lit -- read into the vocabulary's words, through `call_image_figure`. A caption typed in the panel is the figure's; `level` is no argument of an image and is left out."""
    options = {}
    if values.get("detail-figure"):
        # the words ticked in the panel (display_options, UI-002), one or several
        words = values["detail-figure"]
        options["detail_figure"] = [words] if isinstance(words, str) else list(words)
    else:
        shown = {"image-static-model": ("loads", "dimensions"), "image-schema": ("aids",)}.get(command, ())
        if shown and any(w in values for w in shown):
            options["detail_figure"] = [w for w in shown if values.get(w, True) is not False]
    for key in ("highlight", "width"):
        if values.get(key):
            options[key] = values[key]
    return call_image_figure(command, oid, values.get("caption") or caption, **options)


def wrap_figure(expression, caption, oid):
    """`#figure(<expression>, kind: image, caption: [<caption>]) <fig-<oid>>`: a drawing of Woodcore's set as a figure of the report's own (D-16) -- `kind: image`, for the drawing is sized in a `layout` Typst cannot look into, so that it is counted with the report's other pictures."""
    return "#figure(" + expression + ", kind: image, caption: [" + typst_content(caption) + "]) <" + figure_label(oid) + ">"


def call_journal_entries(document=None):
    """The entries read into a variable, for a section that sets a journal its own way -- the newest revision first. `document` is the document whose journal it reads ("cu", "bp" or "rs", the report's by default): the window's own since v0.117, which copied the report's in every document until then."""
    return "#let revisions = " + call_expression("journal-entries", **_given(document=document))


def call_show_annexes(heading=None):
    """The report's annexes, at its end: every source's cover page and the pages it carries. `heading` the level of their heading, False none."""
    return call_command("show-annexes", **_given(heading=_NONE if heading is False else heading))


# --- the new forms a «Copier» button copies (spec 2026-10-21-commandes-typst-refonte, UI-002) ---

def call_include_domain(kind, oid):
    """A domain Woodcore wrote out, included where the section prints it: `#include domain-file("<kind>", "<id>")` (ARCH-008) -- a member check (`check`), a steel check (`steel`), a load (`snow-load`, …, `live-load`), a connector, a polar moment (`connection`), a script."""
    return f"#include domain-file({typst_str(kind)}, {typst_str(oid)})"


def call_domain_loop(kind, ids_kind=None):
    """Every domain of `kind` Woodcore wrote out, the loop a section that prints them all is written as: `#for id in ids("<ids_kind>") { include domain-file("<kind>", id) }` -- `ids_kind` the kind `ids` lists them by where it differs (`check-member` for `check`)."""
    return f"#for id in ids({typst_str(ids_kind or kind)}) {{\n  include domain-file({typst_str(kind)}, id)\n}}"


def call_var_domain(domain, instance, name, **options):
    """One value of the export, read live by `#var` from its calculation: `#var("<name>", domain: ("<domain>", "<instance>"))` (REQ-009: `#val`, `#show-input`, `#var-of` and `#value-of` merged into it); `options` are var's named arguments."""
    return call_command("var", name, domain=(domain, instance), **_given(**options))


def call_figure_loop(command, ids_kind):
    """Every drawing of a kind, each a native figure captioned with its id: `#for id in ids("<ids_kind>") { figure(image-…(id), kind: image, caption: [#id]) }` (REQ-013)."""
    return f"#for id in ids({typst_str(ids_kind)}) {{\n  figure({command}(id), kind: image, caption: [#id])\n}}"
