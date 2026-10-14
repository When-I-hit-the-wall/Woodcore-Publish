"""The Typst call each row of the reference workbook offers -- a value written as Typst, then one function per command (call_show_calc, call_val, call_show_plan …) building its call from the export -- split out of calc/tools/build_reference.py (issue #30), moved verbatim. build_reference.py imports every name back.
"""

import functools
import re
from pathlib import Path
try:
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
        lib_records,
        parse_bindings,
        parse_doc_block,
        parse_doc_comments,
        parse_param_docs,
        read_binding,
        read_signature,
        split_params,
        value_signature,
    )
except ImportError:   # the export imports build_reference as tools.build_reference, calc/tools not on its path
    from tools.build_reference_lib import (  # split out of this module (issue #30): every name it had is still importable from it
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
        lib_records,
        parse_bindings,
        parse_doc_block,
        parse_doc_comments,
        parse_param_docs,
        read_binding,
        read_signature,
        split_params,
        value_signature,
    )


# The program (000-Python/): its lib/ is what the catalogue documents. The data it lists the calls of is the project's, handed in by the caller (v0.81).
ROOT = Path(__file__).resolve().parent.parent.parent


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


def call_show_calc(domain, instance, level=None, title=True, **options):
    """`level` forces a level for this one call; `title=False` passes `title: none` (no heading), a string replaces it."""
    return call_command("show-calc", domain, instance, **_given(level=level, title=_NONE if title is False else (title if isinstance(title, str) else None), **options))


def call_show_input(domain, instance, name):
    return f"#show-input({_args(domain, instance, name)})"


def call_val(name, domain=None, instance=None, type_=None, **options):
    """One value printed, wherever it comes from (docs/typst/formulas.md §10quinquies).

    `domain` alone is a domain of the report -- a `var-domain`'s name; `domain` with
    `instance` is a calculation and its instance, written as the pair `val` reads,
    `#val("s_k", domain: ("snow-load", "SL"))`. `type_` is one of val's four parts.
    Replaced call_inline_value and call_live_load in v0.80, when one command became
    the one that prints one value. `options` are val's other named arguments (v0.117: unit, symbol, level, label, descr, norm, norm_ref, note, style).
    """
    where = None
    if domain is not None and instance is not None:
        where = (domain, instance)
    elif domain is not None:
        where = domain
    return call_command("val", name, **_given(domain=where, type=type_, **options))


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


def call_var(domain, instance, name, symbol=None, **options):
    """A value of the export, written into the registry of variables a report computes with.

    `#var("a_k", var-of("dead-load", "EL+AL-Vordach", "ak"))` prints the value like any other
    variable *and* makes it citable by name in a `#eq` formula below it -- which is what ties a
    hand-written calculation back to the workbook (section 10quinquies). `options` are var's named arguments (v0.117).
    """
    return call_command("var", registry_key(name, symbol), Raw(f"var-of({_args(domain, instance, name)})"), **_given(**options))


def call_var_of(domain, instance, name):
    """The bare object, for a caller that wants it outside the registry -- passing it to a show-* function, or computing with it in a plain `#let`."""
    return f"#let {typst_ident(name)} = var-of({_args(domain, instance, name)})"


def call_value_of(domain, instance, name):
    return f"#let {typst_ident(name)} = value-of({_args(domain, instance, name)})"


def call_show_check(domain, instance, check_name):
    return f"#show-check({_args(domain, instance, check_name)})"


def call_show_live_load(category, level=None, title=None):
    """The live load of one category of SIA 261's Tabelle 8 (docs/domain/loads.md §3.3septies): `#show-live-load("A1")`. `title` is a heading to print above it, False none."""
    return call_command("show-live-load", category, **_given(level=level, title=_NONE if title is False else title))


def call_instance_loop(domain):
    """Every case of a domain, the loop Sections/004-einwirkungen.typ is written as -- a sheet copied in Excel joins it with no edit."""
    d = typst_str(domain)
    return f"#for sheet in instance-ids({d}) {{\n  show-calc({d}, sheet)\n}}"


def typst_number(value):
    """A number as Typst source: no trailing `.0`, no exponent -- `7.5`, `25`, `-6.6`."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"not a number: {value!r}")
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


def call_show_polar_moment(connection, N=0, V=0, M=0, level=None, title=None, width=None):
    """The forces in a connection's fasteners (docs/domain/connections.md §3.3quinquies): N and V in kN, M in kNm, always written out so the call says what it distributes. `width` is Typst source (`60%`), `title` False none."""
    return call_command("show-polar-moment", connection, always=("N", "V", "M"), N=N, V=V, M=M,
                        **_given(level=level, title=_NONE if title is False else title, width=Raw(width) if width else None))


def call_show_connector(connector, description=False, level=None):
    """One connector (docs/domain/connectors.md §3.3nonies); `description=True` adds the row's free text."""
    return call_command("show-connector", connector, description=bool(description), **_given(level=level))


def call_show_connector_resistance(connector, level=None, title=None, width=None):
    """The shear resistance of one connector, SIA 265 6.2.1 (docs/domain/connectors.md §3.3nonies). `width` is Typst source, `title` False none."""
    return call_command("show-connector-resistance", connector, **_given(level=level, title=_NONE if title is False else title, width=Raw(width) if width else None))


def call_show_check_member(check_id, level=None, member_level=None, description=None, title=None, unit=None, shown=None):
    """A member check saved in Woodcore, computed in the report (calc/domains/member_check.py, lib/timber.typ). Only what differs from show-check-member's defaults is written out: `member_level` None leaves the member line at its default (1) and False writes `none`; `title` None leaves it auto and False writes `none`; `description` True writes `true`; `shown` -- {key: level} -- is written at level -1 alone (issue #20), empty there as `(:)`."""
    return call_command("show-check-member", check_id, **_given(
        level=_NONE if level is False else level, shown=dict(shown or {}) if level == -1 else None, member_level=_NONE if member_level is False else member_level,
        description=True if description else None, title=_NONE if title is False else title, unit=_NONE if unit is False else unit))


def call_check_member_loop():
    """Every member check saved in Woodcore, the loop a section showing all of them is written as -- one saved in Woodcore joins it with no edit."""
    return "#for id in check-member-ids() {" + chr(10) + "  show-check-member(id)" + chr(10) + "}"


def call_show_check_steel(check_id, level=None, title=None, unit=None, shown=None):
    """A steel check saved in Woodcore's «Acier» tabs, printed as the export computed it (calc/domains/steel_check.py, lib/steel.typ). Only what differs from show-check-steel's defaults is written out: `title` None leaves it auto and False writes `none`; `unit` "%" writes it; `shown` -- {key: level} -- is written at level -1 alone."""
    return call_command("show-check-steel", check_id, **_given(
        level=_NONE if level is False else level, shown=dict(shown or {}) if level == -1 else None,
        title=_NONE if title is False else title, unit=unit or None))


def call_check_steel_loop():
    """Every steel check saved in Woodcore, the loop a section showing all of them is written as."""
    return "#for id in check-steel-ids() {" + chr(10) + "  show-check-steel(id)" + chr(10) + "}"


def call_connector_loop():
    """Every connector, the loop a section showing all of them is written as -- one created in Woodcore joins it with no edit."""
    return "#for c in connector-ids() {\n  show-connector-resistance(c)\n}"


def call_show_plan(plan, highlight=None, detail=False, legend=True, width=None, axes=True, zoom=None, scale_bar=True, caption=None, dimensions=True, lengths=True):
    """A position plan drawn in Woodcore (docs/domain/position-plans.md §3.3sexies). `highlight` is a position number or a list of them; `detail` frames them; `width` is Typst source (`60%`); `caption` is None for show-plan's own (auto), False for `none` (no figure round the plan) or the text that replaces it; only what differs from show-plan's defaults is written out."""
    labels = list(highlight) if isinstance(highlight, (list, tuple)) else ([highlight] if highlight else [])
    marked = (tuple(labels) if len(labels) > 1 else labels[0]) if labels else None
    return call_command("show-plan", plan, **_given(
        width=Raw(width) if width else None, legend=bool(legend), highlight=marked, detail=bool(detail),
        zoom=zoom, axes=bool(axes), dimensions=bool(dimensions), lengths=bool(lengths), scale_bar=bool(scale_bar), caption=_caption(caption)))


def call_show_plan_legend(plan):
    return f"#show-plan-legend({typst_str(plan)})"


def call_plan_loop():
    """Every plan, the loop Sections/003-baustoffe.typ is written as -- a plan saved in Woodcore joins it with no edit."""
    return "#for p in plan-ids() {\n  show-plan(p)\n}"


def call_show_fire_plan(plan, legend=True, width=None, scale_bar=True, caption=None):
    """A fire-protection plan drawn in Woodcore (v0.115). `width` is Typst source (`60%`); `caption` is None for show-fire-plan's own (auto), False for `none` (no figure round the plan) or the text that replaces it; only what differs from show-fire-plan's defaults is written out."""
    return call_command("show-fire-plan", plan, **_given(width=Raw(width) if width else None, legend=bool(legend), scale_bar=bool(scale_bar), caption=_caption(caption)))


def _caption(caption):
    """A figure's caption as the calls take it: None or "" the command's own (auto), False `none`, a text that text."""
    if caption is None or caption == "":
        return None
    return _NONE if caption is False else caption


def call_fire_plan_loop():
    """Every fire-protection plan -- one saved in Woodcore joins the loop with no edit."""
    return "#for p in fire-plan-ids() {\n  show-fire-plan(p)\n}"


def call_calc_block_plan(position, plan="auto"):
    """A calculation block for a position, with the plan it is drawn on in its header -- `plan="auto"` every plan showing it, a plan id that one."""
    shown = "auto" if plan == "auto" else typst_str(plan)
    return f"#calc-block({typst_str(position)}, plan: {shown})[\n  \n]"


def call_show_static_model(model, width=None, loads=True, highlight=None, caption=None, dimensions=True):
    """A static model drawn in Woodcore (docs/domain/static-models.md §3.3octies). `highlight` is an id the model carries or a list of them; `width` is Typst source (`60%`); `caption` as show-plan's (_caption) -- a text written as a string since v0.117, raw until then; only what differs from show-static-model's defaults is written out."""
    ids = list(highlight) if isinstance(highlight, (list, tuple)) else ([highlight] if highlight else [])
    marked = (tuple(ids) if len(ids) > 1 else ids[0]) if ids else None
    return call_command("show-static-model", model, **_given(
        width=Raw(width) if width else None, loads=bool(loads), dimensions=bool(dimensions), highlight=marked, caption=_caption(caption)))


def call_static_model_loop():
    """Every static model, the loop Sections/005-tragwerksanalyse.typ is written as -- a model saved in Woodcore joins it with no edit."""
    return "#for s in static-model-ids() {\n  show-static-model(s)\n}"


def call_show_schema(schema, width=None, highlight=None, aids=True, caption=None):
    """A detail schema drawn in Woodcore's «Schémas» tab (docs/domain/detail-schemas.md §3.3decies). `highlight` is an id the schema carries or a list of them; `width` is Typst source (`60%`); `aids` False writes `aids: false` -- the default being true, `aids: true` was all this wrote until v0.117, a call that changed nothing; only what differs from show-schema's defaults is written out."""
    ids = list(highlight) if isinstance(highlight, (list, tuple)) else ([highlight] if highlight else [])
    marked = (tuple(ids) if len(ids) > 1 else ids[0]) if ids else None
    return call_command("show-schema", schema, **_given(width=Raw(width) if width else None, highlight=marked, aids=bool(aids), caption=_caption(caption)))


def call_schema_loop():
    """Every schema, the loop for a section that lists every detail -- one drawn in Woodcore joins it with no edit."""
    return "#for id in schema-ids() {\n  show-schema(id)\n}"


def call_show_journal(form=None, level=None, title=None):
    """The report's revision journal, written in Woodcore's «Journal» tab (docs/domain/journal.md §3.3terdecies). `form` is "table", "list" or "grid"; `title` a text (a string since v0.117, raw until then), False none; only what differs from show-journal's defaults is written out, and the journal takes no id -- there is one per project."""
    return call_command("show-journal", **_given(form=form, level=level, title=_NONE if title is False else title))


def call_journal_entries(document=None):
    """The entries read into a variable, for a section that sets a journal its own way -- the newest revision first. `document` is the document whose journal it reads ("cu", "bp" or "rs", the report's by default): the window's own since v0.117, which copied the report's in every document until then."""
    return "#let revisions = " + call_expression("journal-entries", **_given(document=document))


def call_show_extract(excerpt, width=None, caption=None):
    """An excerpt of an annex, framed in Woodcore's «Annexes» tab (docs/domain/annexes.md §3.3undevicies); `caption` as show-plan's (a string since v0.117); only what differs from show-extract's defaults is written out."""
    return call_command("show-extract", excerpt, **_given(width=Raw(width) if width else None, caption=_caption(caption)))


def call_show_annexes(heading=None):
    """The report's annexes, at its end: every source's cover page and the pages it carries. `heading` the level of their heading, False none."""
    return call_command("show-annexes", **_given(heading=_NONE if heading is False else heading))


def call_show_load_summary(title=None):
    """The table of every area load the report lists (lib/summary.typ, v0.117 in the window): `title` a text, False none."""
    return call_command("show-load-summary", **_given(title=_NONE if title is False else title))


def call_show_line_load_summary(title=None):
    """The table of every line load the report lists (lib/summary.typ): `title` a text, False none."""
    return call_command("show-line-load-summary", **_given(title=_NONE if title is False else title))


def call_show_position_list(scope=None, plans=None, storey=None, title=None, columns=None, widths=None, legend=None):
    """The list of the positions (lib/positions.typ, v0.116; in the window since v0.117): `scope` "all" or "plans", `plans` the plans whose positions it lists, `storey` one storey, `title` a text or False for none, `columns` the columns printed by name, `widths` a width for some of them (`{"id": Raw("30mm")}`), `legend` a text set under the table."""
    return call_command("show-position-list", **_given(scope=scope, plans=tuple(plans) if plans else None, storey=storey, title=_NONE if title is False else title,
                                                        columns=tuple(columns) if columns else None, widths=widths or None, legend=legend))


def call_extract_loop():
    """Every excerpt, the loop for a section that shows them all -- one framed in Woodcore joins it with no edit."""
    return "#for id in extract-ids() {\n  show-extract(id)\n}"
