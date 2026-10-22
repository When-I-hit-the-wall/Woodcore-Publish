"""An export sheet's objects written in raw Typst (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, REQ-019, Q-013, Q-015): each one a `#place(top + left, dx: …, dy: …, …) <sheet-…>` -- read into the call the sheet editor's models edit (`from_place`), and written back from it (`to_place`).

The engineer, Q-015 (21.10.2026): «#place brut». The page stays `#show: sheet.with(…)`, the internal primitive whose `show place` rule tells the editor where each object labelled `<sheet-…>` stands (lib/sheet.typ); what a `#place` holds is a command of the report's own or plain Typst:

* a text -- `text(size: 16pt, weight: "bold")[…]`, in a `box(width: …)[…]` where it wraps;
* a plan, a fire-protection plan -- `image-positions-plan(id, scale: 100, title: auto, …)`, `image-fire-plan(…)`, their sheet's mode;
* a section, a legend, the title block -- `image-section(…)`, `image-legend(…)`, `image-titleblock(…)`, the title block placed at the bottom right of the paper where its place is the sheet's own;
* the list of the positions and the quantities -- `box(width: …)[#include "/Positions/position-list.typ"]`, the files written once (calc/domains/list_files.py).

What has no raw form is left out (Q-015): the short caption under a plan, the level of each object, a list's plans and scope -- the list is the project's.

The calls are those of lib/sheet.typ's `sheet-*` commands, which the models of calc/typst_objects_sheets.py know: a sheet written before is read as it is, and written back in this form at its next change. Qt-free.
"""

import copy

import typst_calls
from typst_objects_parse import AUTO, Call, Content, Length, ParseError, _Parser, inline, parse_value

# The objects of a sheet that are placed -- every one but the page.
PLACED = ("sheet-text", "sheet-viewport", "sheet-section", "sheet-legend", "sheet-fire-viewport", "sheet-fire-legend",
          "sheet-position-list", "sheet-quantities", "sheet-titleblock")
# The lists' files from the Typst root, in a project laid out by folders (list_files.path)
LIST_FILES = {"sheet-position-list": "/Positions/position-list.typ", "sheet-quantities": "/Positions/quantities.typ"}
# Where the title block stands where its place is the sheet's own: the bottom right corner, inside the frame's default margin
CORNER = Length(-10, "mm")
# The words of `detail-figure` a viewport's switches are
FIGURE_WORDS = (("length", "lengths"), ("axes", "axes"), ("dimensions", "dimensions"), ("centres", "centres"))
TITLEBLOCK_FIELDS = ("logo", "object", "element", "client", "architect", "phase", "project-number", "plan-number", "index", "revision-date",
                     "revision-author", "modification", "drawn-by", "date", "scale", "size")


def _named(pairs):
    return ", ".join(f"{name}: {inline(value)}" for name, value in pairs)


def _call(name, positional=(), pairs=()):
    parts = [inline(v) for v in positional] + [f"{n}: {inline(v)}" for n, v in pairs]
    return f"{name}({', '.join(parts)})"


def _is(value, default):
    return value is default or value == default


def inner(call):
    """What the `#place` of the object `call` holds, as Typst code."""
    a = call.args
    kind = call.type
    if kind == "sheet-text":
        pairs = [(n, a[n]) for n, d in (("size", Length(10, "pt")), ("weight", "regular")) if n in a and not _is(a[n], d)]
        body = a.get("body")
        # never `text[…]`: the size is written where it is the default, so that the call has its parentheses
        text = "text(" + (_named(pairs) if pairs else "size: 10pt") + ")[" + (body.markup if isinstance(body, Content) else "" if body is None else str(body)) + "]"
        width = a.get("width", AUTO)
        return text if width is AUTO else f"box(width: {inline(width)})[#{text}]"
    if kind in ("sheet-viewport", "sheet-fire-viewport"):
        pairs = []
        size = [("scale", a["scale"])] if a.get("scale") is not None else [("width", a["width"])] if a.get("width") is not None else []
        pairs += size
        if kind == "sheet-viewport":
            if a.get("highlight") not in (None, []):
                pairs.append(("highlight", a["highlight"]))
            shown = [word for word, name in FIGURE_WORDS if a.get(name, True) is not False]
            if len(shown) != len(FIGURE_WORDS):
                pairs.append(("detail-figure", tuple_of(shown)))
            pairs.append(("detail-legend", "scale-bar" if a.get("scale-bar") is True else "none"))
            name = "image-positions-plan"
        else:
            under = (["objects"] if a.get("legend", AUTO) is not False else []) + (["scale-bar"] if a.get("scale-bar") is True else [])
            pairs.append(("detail-legend", tuple_of(under) if under else "none"))
            name = "image-fire-plan"
        pairs.append(("title", a.get("title", AUTO)))
        return _call(name, [a.get("plan")], pairs)
    if kind == "sheet-section":
        pairs = [(n, a[n]) for n in ("storey", "scale", "width") if a.get(n) is not None]
        if "title" in a and a["title"] is not AUTO:
            pairs.append(("title", a["title"]))
        return _call("image-section", [a.get("plan")], pairs)
    if kind in ("sheet-legend", "sheet-fire-legend"):
        pairs = [("plans", a["plans"])] if "plans" in a and a["plans"] is not AUTO else []
        if kind == "sheet-fire-legend":
            pairs.append(("kind", "fire"))
        if "width" in a and not _is(a["width"], Length(120, "mm")):
            pairs.append(("width", a["width"]))
        if "title" in a and a["title"] is not AUTO:
            pairs.append(("title", a["title"]))
        return _call("image-legend", (), pairs)
    if kind in LIST_FILES:
        width = a.get("width", Length(180 if kind == "sheet-position-list" else 150, "mm"))
        return f'box(width: {inline(width)})[#include "{LIST_FILES[kind]}"]'
    if kind == "sheet-titleblock":
        pairs = [(n, a[n]) for n in ("width",) + TITLEBLOCK_FIELDS if n in a]
        return _call("image-titleblock", (), pairs)
    raise ValueError(f"{kind!r} is no object placed on a sheet")


def tuple_of(words):
    return words[0] if len(words) == 1 else tuple(words)


def to_place(call):
    """The body of the object `call` on a sheet: `#place(top + left, dx: …, dy: …,\\n  …) <kind>` -- the title block at the bottom right corner where its place is its own."""
    a = call.args
    if call.type == "sheet-titleblock" and a.get("x", AUTO) is AUTO and a.get("y", AUTO) is AUTO:
        head = f"#place(bottom + right, dx: {inline(CORNER)}, dy: {inline(CORNER)},"
    else:
        x = a.get("x", Length(0, "mm"))
        y = a.get("y", Length(0, "mm"))
        head = f"#place(top + left, dx: {inline(_mm(x))}, dy: {inline(_mm(y))},"
    return head + "\n  " + inner(call) + ") <" + call.type + ">"


def _mm(value):
    """A coordinate as a length: a number of millimetres written as one."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return Length(value, "mm")
    return value


def _sub_call(text):
    """`name(…)[…]` read as a Call, its positional arguments and its content block kept."""
    found, end = _Parser("#" + text.strip()).call(0, positional=True)
    if end != len(text.strip()) + 1:
        raise ParseError("the object's #place holds one call and nothing after it", end, text)
    return found


def from_place(body, kind):
    """The call of the sheet's object `kind` the raw `#place` `body` is, as `to_place` writes it -- a ParseError where it is not one of these forms."""
    text = body.strip()
    if not text.startswith("#place("):
        raise ParseError("the object is no #place(…)", 0, body)
    close = typst_calls.closing(text, len("#place"))
    if close is None:
        raise ParseError("the #place( is never closed", 0, body)
    label = text[close + 1:].strip()
    if label != f"<{kind}>":
        raise ParseError(f"the #place is labelled {label or 'nothing'} -- <{kind}> says what it is", close, body)
    # a comment written in the call is read past (the object is then hand-edited: Woodcore's form has none)
    args = typst_calls.mask_comments(text[len("#place") + 1:close])
    parts = [args[x:y].strip() for x, y in typst_calls.split(args) if args[x:y].strip()]
    if len(parts) != 4 or not parts[1].startswith("dx:") or not parts[2].startswith("dy:"):
        raise ParseError("the #place is written `#place(top + left, dx: …, dy: …, …)`", 0, body)
    align = " ".join(parts[0].split())
    dx, dy = parse_value(parts[1][3:]), parse_value(parts[2][3:])
    held = _sub_call(parts[3])
    out = {}
    if align == "bottom + right" and kind == "sheet-titleblock":
        out.update(x=AUTO, y=AUTO)
    elif align == "top + left":
        out.update(x=dx, y=dy)
    else:
        raise ParseError(f"a sheet's object is placed from its top left corner -- got {align}", 0, body)
    a = dict(held.args)
    if kind == "sheet-text":
        width = AUTO
        if held.type == "box":
            width = a.get("width", AUTO)
            held = _sub_call(held.body.markup.lstrip("#")) if isinstance(held.body, Content) and held.body.markup.startswith("#text") else held
            a = dict(held.args)
        if held.type != "text":
            raise ParseError(f"a text of the sheet is text(…)[…] -- got {held.type}", 0, body)
        out["body"] = held.body if isinstance(held.body, Content) else None
        for name in ("size", "weight"):
            if name in a:
                out[name] = a[name]
        if width is not AUTO:
            out["width"] = width
    elif kind in ("sheet-viewport", "sheet-fire-viewport"):
        want = "image-positions-plan" if kind == "sheet-viewport" else "image-fire-plan"
        if held.type != want:
            raise ParseError(f"a plan of the sheet is {want}(…) -- got {held.type}", 0, body)
        out["plan"] = held.positional[0] if held.positional else None
        for name in ("scale", "width"):
            if name in a:
                out[name] = a[name]
        under = _words(a.get("detail-legend", "none"))
        if kind == "sheet-viewport":
            if "highlight" in a:
                out["highlight"] = a["highlight"]
            shown = _words(a["detail-figure"]) if "detail-figure" in a else [w for w, _n in FIGURE_WORDS]
            for word, name in FIGURE_WORDS:
                if word not in shown:
                    out[name] = False
        else:
            if "objects" not in under:
                out["legend"] = False
        if "scale-bar" in under:
            out["scale-bar"] = True
        if "title" in a and a["title"] is not AUTO:
            out["title"] = a["title"]
    elif kind == "sheet-section":
        if held.type != "image-section":
            raise ParseError(f"a section of the sheet is image-section(…) -- got {held.type}", 0, body)
        out["plan"] = held.positional[0] if held.positional else None
        out.update({n: a[n] for n in ("storey", "scale", "width", "title") if n in a})
    elif kind in ("sheet-legend", "sheet-fire-legend"):
        if held.type != "image-legend" or (a.get("kind", "position") == "fire") != (kind == "sheet-fire-legend"):
            raise ParseError(f"a legend of the sheet is image-legend(…) of its kind -- got {held.type}", 0, body)
        out.update({n: a[n] for n in ("plans", "width", "title") if n in a})
    elif kind in LIST_FILES:
        if held.type != "box" or not isinstance(held.body, Content) or LIST_FILES[kind] not in held.body.markup:
            raise ParseError(f"a list of the sheet is box(width: …)[#include \"{LIST_FILES[kind]}\"]", 0, body)
        if "width" in a:
            out["width"] = a["width"]
    elif kind == "sheet-titleblock":
        if held.type != "image-titleblock":
            raise ParseError(f"the title block is image-titleblock(…) -- got {held.type}", 0, body)
        out.update({n: a[n] for n in ("width",) + TITLEBLOCK_FIELDS if n in a})
    return Call(kind, copy.deepcopy(out))


def _words(value):
    if isinstance(value, str):
        return [value]
    return list(value) if isinstance(value, (list, tuple)) else []
