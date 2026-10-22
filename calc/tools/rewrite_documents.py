"""The documents' templates and the example project carried into raw Typst, once (spec docs/requirements/completed/2026-10-21-commandes-typst-refonte.md, lot 18, REQ-017, REQ-019, Q-002, Q-007): a **local tool**, run by hand on the repository's files and never by Woodcore -- a project of the engineer's is never rewritten (REQ-020: an alert, no migration).

    python calc/tools/rewrite_documents.py <folder> [<folder> …]

Each tagged object of a `#doc-*` command becomes raw Typst under the same tag's id, written the way the «Structure du document» tab reads it back (calc/typst_raw_table.py, calc/typst_objects.py):

* `#doc-table`, `#dead-load-table`, `#live-load-table`, `#doc-signatures` -- a `table` object: `#figure(table(…), caption: […])`, the engine's three rules as `table.hline`, the columns' widths and alignments as `render-table` gave them, hidden columns in their comment; the live loads' category and values each in a `#sync` (Q-007), the value a reading of the export; their notes a paragraph after it;
* `#doc-choice` -- a paragraph: the label and the answer, or, none chosen yet, the options as a list for the engineer to keep one (Q-002: no parametric choice);
* `#doc-checklist` -- a paragraph: the label and the list of what is ticked, each with its text (Q-002);
* `#doc-image` -- a paragraph holding its `#figure(image(…))`, or a frame where there is no picture yet;
* `#doc-annexes` -- a paragraph holding `#show-annexes(…)`.

The calls left in the sections: `#show-journal()` becomes the document's journal written once, `#include domain-file("journal", "<document>")` (calc/domains/list_files.py, ARCH-008); a case of a load's `show-calc` its file, `include domain-file(kind, id)` (ARCH-008). Every byte outside what changes is kept, line endings included.
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CALC = HERE.parent
for path in (str(CALC), str(HERE)):
    if path not in sys.path:
        sys.path.insert(0, path)

import typst_objects as to  # noqa: E402
from i18n import strings  # noqa: E402
from typst_objects_parse import AUTO, Content, Expr, Length, inline  # noqa: E402

THICK, THIN = "table.hline(stroke: 1pt)", "table.hline(stroke: 0.5pt)"
KIND_WIDTH = {"wide": "1fr"}
KIND_ALIGN = {"number": "right", "value": "right", "math": "center"}
LIVE_COLUMNS = {"zone": ("document.zone", "text"), "storey": ("document.storey", "text"), "use": ("document.use", "wide"),
                "category": ("document.category", "math"), "q_k": (None, "number"), "Q_k": (None, "number")}
LIVE_SYMBOLS = {"q_k": "$q_k$ [kN/m²]", "Q_k": "$Q_k$ [kN]"}
DEAD_COLUMNS = {"zone": ("document.zone", "text"), "storey": ("document.storey", "text"), "buildup": ("document.buildup", "wide"),
                "load": ("document.superimposed", "number")}


def markup(value):
    """A value of a call as markup: content as written, a string or a number as text, nothing as nothing."""
    if value is None or value is AUTO:
        return ""
    if isinstance(value, Content):
        return value.markup
    if isinstance(value, Expr):
        return "#" + value.code if hasattr(value, "code") else str(value)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return inline(value)
    return str(value)


def raw_table(columns, rows, caption, header=True, hidden=(), lang="de", bold_rows=()):
    """A table object's body: `#figure(table(…), caption: […])` -- `columns` [(title markup, kind)], `rows` [[cell markup]], the hidden columns (by index) in the comment at the end of each line."""
    shown = [i for i in range(len(columns)) if i not in hidden]
    widths = [KIND_WIDTH.get(columns[i][1], "auto") for i in shown]
    aligns = [KIND_ALIGN.get(columns[i][1], "left") for i in shown]

    def tail(cells):
        parts = [f"{i + 1}=[{cells[i]}]" for i in hidden]
        return ("  // woodcore:hidden " + " ".join(parts)) if parts else ""

    inner = "    "
    lines = ["#figure(", "  table(",
             inner + "columns: (" + ", ".join(widths) + (",)" if len(widths) == 1 else ")") + ",",
             inner + "align: (" + ", ".join(aligns) + (",)" if len(aligns) == 1 else ")") + ",",
             inner + THICK + ","]
    if header:
        lines.append(inner + "table.header(" + ", ".join(f"[*{columns[i][0]}*]" if columns[i][0] else "[]" for i in shown) + ")," + tail([c[0] for c in columns]))
        lines.append(inner + THIN + ",")
    for r, row in enumerate(rows):
        cells = [f"[*{row[i]}*]" if r in bold_rows and row[i] else f"[{row[i]}]" for i in shown]
        lines.append(inner + ", ".join(cells) + "," + tail(row))
    lines.append(inner + THICK + ",")
    lines.append("  ),")
    if caption:
        lines.append(f"  caption: [{caption}],")
    lines.append(")")
    return "\n".join(lines)


def notes_text(notes):
    """The notes of a table, a paragraph after it."""
    items = notes if isinstance(notes, (list, tuple)) else [notes]
    parts = [markup(n) for n in items if n is not None]
    return " ".join(p for p in parts if p) or None


def convert_doc_table(call, lang):
    a = call.args
    cols = a.get("columns") or []
    hidden_ids = list(a.get("hidden") or [])
    columns = [(markup(c.get("title")), c.get("kind", "text")) for c in cols]
    ids = [c.get("id") for c in cols]
    rows = [[markup(r.get(cid)) for cid in ids] for r in (a.get("rows") or [])]
    body = raw_table(columns, rows, markup(a.get("caption")), header=a.get("header", True) is not False,
                     hidden=[i for i, cid in enumerate(ids) if cid in hidden_ids], lang=lang)
    return body, notes_text(a.get("notes"))


def convert_load_table(call, lang, live):
    a = call.args
    known = LIVE_COLUMNS if live else DEAD_COLUMNS
    cols = a.get("columns") or [{"id": k} for k in known]
    ids = [c.get("id") for c in cols]
    hidden_ids = list(a.get("hidden") or [])
    columns = []
    for c in cols:
        word, kind = known.get(c.get("id"), (None, c.get("kind", "text")))
        title = markup(c.get("title")) if c.get("title") is not None else (LIVE_SYMBOLS.get(c["id"]) if live and c["id"] in LIVE_SYMBOLS else strings.text(word, lang) if word else c.get("id"))
        columns.append((title, c.get("kind", kind)))
    rows, synced = [], set()
    for r in a.get("rows") or []:
        cells = []
        category = r.get("category")
        for cid in ids:
            value = r.get(cid)
            if live and cid == "category" and isinstance(category, str):
                ident = f"live-load/{category}/kategorie"
                cells.append(f'#sync("{ident}")[{category}]' if ident not in synced else category)
                synced.add(ident)
            elif live and cid in ("q_k", "Q_k") and (value is AUTO or value is None) and isinstance(category, str):
                ident = f"live-load/{category}/{cid}"
                # read live from the export (Q-007), its value alone: a `#sync` keeps what its content states at every level, the uniform one included (lib/calc-engine-core.typ)
                reading = f'#var("{cid}", domain: ("live-load", "{category}"), display: "value", label-position: "none", descr-position: "none", norm-position: "none")'
                cells.append(f'#sync("{ident}")[{reading}]' if ident not in synced else reading)
                synced.add(ident)
            else:
                cells.append(markup(value))
        rows.append(cells)
    body = raw_table(columns, rows, markup(a.get("caption")), hidden=[i for i, cid in enumerate(ids) if cid in hidden_ids], lang=lang)
    return body, notes_text(a.get("notes"))


def convert_signatures(call, lang):
    a = call.args
    place_date = a.get("place-date", True) is not False
    columns = [(strings.text("document.role", lang), "text"), (strings.text("document.name", lang), "text")]
    if place_date:
        columns.append((strings.text("document.place_date", lang), "text"))
    columns.append((strings.text("document.signature", lang), "wide"))
    rows, bold, group = [], [], None
    for r in a.get("rows") or []:
        here = markup(r.get("group")) if r.get("group") is not None else None
        if here is not None and here != group:
            bold.append(len(rows))
            rows.append([here] + [""] * (len(columns) - 1))
        group = here
        when = ", ".join(x for x in (markup(r.get("place")), markup(r.get("date"))) if x)
        row = [markup(r.get("role")), markup(r.get("name"))] + ([when] if place_date else []) + ["#v(1cm)#line(length: 100%, stroke: 0.5pt)"]
        rows.append(row)
    return raw_table(columns, rows, None, lang=lang, bold_rows=bold), None


def colon(lang):
    """The colon after a label: French puts a narrow no-break space before it, as the templates' prose does."""
    return "\u202f:" if lang == "fr" else ":"


def convert_choice(call, lang):
    a = call.args
    label = markup(a.get("label")) if a.get("label") is not None else None
    options = a.get("options") or []
    selected = a.get("selected")
    if selected is not None:
        answer = next((markup(o.get("label")) for o in options if o.get("id") == selected), "")
    elif a.get("other") is not None:
        answer = markup(a["other"])
    else:
        answer = None
    if answer is not None:
        return (f"*{label}*{colon(lang)} {answer}" if label else answer), None
    # none chosen yet: the options, for the engineer to keep the one that holds (Q-002)
    head = [f"*{label}*{colon(lang)}"] if label else []
    return "\n".join(head + [f"- {markup(o.get('label'))}" for o in options] or ["[…]"]), None


def convert_checklist(call, lang):
    a = call.args
    label = markup(a.get("label")) if a.get("label") is not None else None
    only = a.get("only-checked", True) is not False
    lines = [f"*{label}*{colon(lang)}"] if label else []
    for o in a.get("options") or []:
        checked = o.get("checked", False) is True
        if only and not checked:
            continue
        text = markup(o.get("text")) if o.get("text") is not None else ""
        mark = "" if only else ("☒ " if checked else "☐ ")
        lines.append(f"- {mark}*{markup(o.get('label'))}*" + (f" \\ {text}" if text and (checked or only) else ""))
    if len(lines) == (1 if label else 0):
        lines.append("- […]")
    return "\n".join(lines), None


def convert_image(call, lang):
    a = call.args
    caption = markup(a.get("caption")) if a.get("caption") is not None else None
    width = a.get("width", Length(100, "%"))
    if a.get("file"):
        path = a["file"].strip()
        held = f'image("{path if path.startswith("/") else "/" + path}", width: {inline(width)})'
    else:
        words = markup(a.get("placeholder")) if a.get("placeholder") is not None else strings.text("document.image", lang)
        held = f"rect(width: {inline(width)}, height: 5cm, stroke: 0.5pt + luma(60%))[{words}]"
    return "#figure(" + held + (f", caption: [{caption}]" if caption else "") + ")", None


def convert(obj, lang):
    """[(kind, id, body)] in place of the object `obj`, or None where it stays as it is."""
    call = obj.call
    if call is None:
        return None
    if obj.type == "doc-table":
        body, notes = convert_doc_table(call, lang)
    elif obj.type in ("live-load-table", "dead-load-table"):
        body, notes = convert_load_table(call, lang, obj.type == "live-load-table")
    elif obj.type == "doc-signatures":
        body, notes = convert_signatures(call, lang)
    elif obj.type == "doc-choice":
        return [("text", obj.id, convert_choice(call, lang)[0])]
    elif obj.type == "doc-checklist":
        return [("text", obj.id, convert_checklist(call, lang)[0])]
    elif obj.type == "doc-image":
        return [("text", obj.id, convert_image(call, lang)[0])]
    elif obj.type == "doc-annexes":
        heading = call.args.get("heading", 2)
        return [("text", obj.id, "#show-annexes(" + ("" if heading == 2 else f"heading: {inline(heading)}") + ")")]
    else:
        return None
    out = [("table", obj.id, body)]
    if notes:
        out.append(("text", obj.id + "-notes", notes))
    return out


LOOP = re.compile(r"#for (\w+) in ids\(\"(dead-load|snow-load|wind-load|live-load)\"\) \{\n(\s*)show-calc\(\"\2\", \1\)\n\}")


# The loops of the report's template over what the export holds, each printing the domain's own file or image (ARCH-008, REQ-013, REQ-015)
LOOPS = (
    ('#for id in ids("plan") {\n  show-plan(id)\n}',
     '#for id in ids("plan") {\n  figure(image-positions-plan(id), kind: image, caption: context t-str("plan.caption", id: id))\n}'),
    ('#for id in ids("position") {\n  member(id, level: 1, description: true)\n}',
     '#for id in ids("position") {\n  position(id, category-show: ("type", "material", "strength-class", "dimension", "units", "descr"))\n  parbreak()\n}'),
    ('  #for id in ids("connector") {\n    show-connector(id, description: true)\n    parbreak()\n  }',
     '  #for id in ids("connector") {\n    include domain-file("connector", id)\n  }'),
    ('#for id in ids("static-model") {\n  show-static-model(id)\n}',
     '#for id in ids("static-model") {\n  figure(image-static-model(id), kind: image, caption: [#id])\n}'),
    ("// Every position, each on the line #member prints at level 1 -- the timber ones written down for the checks of SIA 265 4.2 on the way --, and every connector saved in Woodcore",
     "// Every position on its line (#position), and every connector saved in Woodcore, its file written out (domain-file)"),
    ("Name the cases by hand instead -- #show-calc(\"snow-load\", \"SL\", level: 1) -- to choose each one's level and leave some out. The live loads are SIA 261's Tabelle 8, one category per call: #show-live-load(\"A1\").",
     "Name the cases by hand instead -- #include domain-file(\"snow-load\", \"SL\") -- to leave some out. The live loads are SIA 261's Tabelle 8, one category a file: #include domain-file(\"live-load\", \"A1\")."),
    ("// A connector's resistance: #show-connector-resistance(\"<id>\").", "// A connector's resistance is in its file, which section 003 includes for every connector -- included once, its lines' ids being its own."),
)


def rewrite_text(text, lang, document="rs"):
    """`text` with its objects carried over and its removed calls replaced -- every other byte kept; `document` the one whose journal a journal section includes."""
    newline = "\r\n" if "\r\n" in text else "\n"
    work = text.replace("\r\n", "\n")
    found = sorted(to.objects(work), key=lambda o: o.start, reverse=True)
    lines = work.split("\n")
    for obj in found:
        new = convert(obj, lang)
        if not new:
            continue
        block = []
        for kind, oid, body in new:
            block += [f"{to.START} {kind} {oid}"] + body.split("\n") + [f"{to.END} {oid}"]
            if kind == "table" and len(new) > 1:
                block.append("")
        lines[obj.start:obj.end + 1] = block
    work = "\n".join(lines)
    work = work.replace("#show-journal()", f'#include domain-file("journal", "{document}")')
    for old, new in LOOPS:
        work = work.replace(old, new)
    work = LOOP.sub(lambda m: f'#for {m.group(1)} in ids("{m.group(2)}") {{\n{m.group(3)}include domain-file("{m.group(2)}", {m.group(1)})\n}}', work)
    return work.replace("\n", newline)


def language_of(path):
    for part in Path(path).parts:
        if part in ("de", "fr", "en"):
            return part
    return "de"


def document_of(path):
    """The document a file of a template belongs to, by its folder (`templates/documents/<document>/…`); the report elsewhere."""
    for part in Path(path).parts:
        if part in ("cu", "bp", "rs"):
            return part
    return "rs"


def main(folders):
    changed = []
    for folder in folders:
        for path in sorted(Path(folder).rglob("*.typ")):
            raw = path.read_bytes().decode("utf-8")
            new = rewrite_text(raw, language_of(path), document_of(path))
            if new != raw:
                path.write_bytes(new.encode("utf-8"))
                changed.append(path)
    for path in changed:
        print(path)
    return changed


if __name__ == "__main__":
    main(sys.argv[1:])
