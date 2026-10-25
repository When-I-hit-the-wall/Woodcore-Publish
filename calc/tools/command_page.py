"""The condensed page of one command, as data: what Woodcore's commands tab turns into widgets and website/build.py into HTML (spec 2026-10-24-onglet-commandes-pages, ARCH-001, ARCH-008; UI-003 to UI-007; docs/typst/command-docs.md §10sexies).

**One page for the window and the site.** The line of the command with its arguments grouped, the key points, the table of the arguments, the two bubbles -- an argument's sentence, and every value it takes with its call and its print --, the search: each is a pure function of the command's record (lib/, build_reference), its page (calc/i18n/command-pages.json, command_pages) and the committed prints of its values (examples/out/values/, build_examples.values_index). Every word it says is calc/i18n/reference.json's (command_docs.word), once for both: the tab's STRINGS keep only the chrome of the window.

**The order of the line.** The positional arguments first, as one writes them -- `#var(key, symbol, value, unit` --, then the named ones a line per group, in the order of the table: what the line holds, what is printed, the label and the description, the citation, the rest; a content block `body` last, between brackets. A default is the signature's, never the page's (REQ-003): the page says what a value does, lib/ what it is.

Nothing here imports Qt (tests/test_command_page.py holds it).
"""

import build_examples as examples  # the committed prints of the values and the examples' measured levels
import build_reference as ref
import command_docs as docs
import command_pages as pages

GROUPS = pages.GROUPS
PER_LINE = 4   # the named arguments of the line of the command, at most so many a line


def word(key, lang, **values):
    return docs.word(key, lang, **values)


def tr(text, lang):
    return pages.tr(text, lang)


def has_page(name, table=None):
    return pages.entry(name, table) is not None


def default_of(record, name, spec):
    return pages.default_of(record, name, spec)


def status_text(record, name, spec, lang):
    """«obligatoire», or «optionnel · par défaut auto»: the head of both bubbles and the table's status."""
    if spec["status"] == "required":
        return word("required", lang)
    default = default_of(record, name, spec)
    text = word("optional", lang)
    return f"{text} · {word('default', lang)} {default}" if default is not None else text


# --- the line of the command --------------------------------------------------------------------------------

def _ordered(page):
    """The page's arguments in the order of the table: group by group, inside each in the page's own order."""
    args = page["arguments"]
    return [(name, args[name]) for group in GROUPS for name in args if args[name]["group"] == group]


def line(record, lang=None, table=None):
    """The line of the command (UI-003), as lines of segments: {"kind": "cmd"|"text"|"arg"|"value", "text", "arg", "required"}. An `arg` segment opens the argument's bubble, a `value` segment the bubble of its values."""
    page = pages.entry(record["name"], table)
    if page is None:
        return None
    if page.get("line"):
        return [[{"kind": "cmd", "text": page["line"]}]]
    positional, named, body = [], {}, None
    for name, spec in _ordered(page):
        if name == "body":
            body = (name, spec)
        elif pages.is_positional(record, name, spec) or name.startswith(".."):
            positional.append((name, spec))
        else:
            named.setdefault(spec["group"], []).append((name, spec))

    def arg(name, spec):
        return {"kind": "arg", "text": name, "arg": name, "required": spec["status"] == "required"}

    first = [{"kind": "cmd", "text": f"#{record['name']}"}, {"kind": "text", "text": "("}]
    for i, (name, spec) in enumerate(positional):
        if i:
            first.append({"kind": "text", "text": ", "})
        first.append(arg(name, spec))
    lines = [first]
    groups = [g for g in GROUPS if g in named]
    # a group of more than PER_LINE arguments goes on as many lines as it needs, so that the line is read without scrolling
    chunks = [named[g][k:k + PER_LINE] for g in groups for k in range(0, len(named[g]), PER_LINE)]
    for i, chunk in enumerate(chunks):
        if positional or i:
            lines[-1].append({"kind": "text", "text": ","})
        current = [{"kind": "text", "text": "  "}]
        for j, (name, spec) in enumerate(chunk):
            if j:
                current.append({"kind": "text", "text": ", "})
            current.append(arg(name, spec))
            current.append({"kind": "text", "text": ": "})
            current.append({"kind": "value", "text": str(default_of(record, name, spec)), "arg": name})
        lines.append(current)
    closing = [{"kind": "text", "text": ")"}]
    if body is not None:
        closing += [{"kind": "text", "text": "["}, arg(*body), {"kind": "text", "text": "]"}]
    if groups:
        lines.append(closing)
    else:
        lines[-1] += closing
    return lines


def line_text(lines):
    """The line as plain text, one line of code a line."""
    return "\n".join("".join(segment["text"] for segment in row) for row in lines)


# --- the page ------------------------------------------------------------------------------------------------

def view(record, lang, table=None):
    """Everything the page of one command shows above its examples, or None where it has no page yet: the head, the line, the key points, the table in groups, the names written by name and a closing note."""
    page = pages.entry(record["name"], table)
    if page is None:
        return None
    groups = []
    for group in GROUPS:
        rows = []
        for name, spec in page["arguments"].items():
            if spec["group"] != group:
                continue
            rows.append({
                "name": name,
                "required": spec["status"] == "required",
                "status": word(spec["status"], lang),
                "default": None if spec["status"] == "required" else default_of(record, name, spec),
                "text": spec["text"][lang],
                "examples": [{"code": tr(e["code"], lang), "shows": e["shows"][lang] if "shows" in e else ""} for e in spec["examples"]],
                "values": bool(spec.get("values")),
            })
        if rows:
            groups.append({"key": group, "label": word(f"group_{group}", lang), "rows": rows})
    named = page.get("named")
    return {
        "name": record["name"],
        "category": record["category"],
        "category_label": docs.category_label(record["category"], lang),
        "lead": page["lead"][lang],
        "line": line(record, lang, table),
        "hint": word("line_hint", lang),
        "keys": [{"title": k["title"][lang], "text": k["text"][lang]} for k in page["keys"]],
        "columns": [word("col_argument", lang), word("col_status", lang), word("col_does", lang)],
        "groups": groups,
        "named": {"label": word("group_named", lang), "text": named["text"][lang], "members": list(named["members"])} if named else None,
        "note": page["note"][lang] if page.get("note") else None,
    }


# --- the bubbles ---------------------------------------------------------------------------------------------

def argument_bubble(record, name, lang, table=None):
    """The bubble of an argument's name (UI-006): its name, its status on the same line, its sentence."""
    spec = pages.entry(record["name"], table)["arguments"][name]
    return {"name": name, "status": status_text(record, name, spec, lang), "text": spec["text"][lang]}


def preview(record, name, value, lang, table=None, index=None):
    """What the bubble of the values shows beside one value (UI-007): its set-up lines, its call, where its print stands in its command's sheet, and what is said instead of or beside the print -- nothing printed, the same print as other values, the role's own note. `state` says whether the committed print matches the call: fresh, stale or missing (REQ-012: never a compile behind the reader's back)."""
    index = examples.values_index() if index is None else index
    if "call" not in value:
        spec = pages.entry(record["name"], table)["arguments"][name]
        return {"setup": "", "call": "", "sheet": None, "file": None, "rect": None, "blank": False, "state": "unrendered",
                "note": spec["unrendered"][lang] if spec.get("unrendered") else None, "same": []}
    setup = tr(value["setup"], lang) if value.get("setup") else ""
    call = tr(value["call"], lang)
    key = examples.value_key(record["name"], name, value["value"])
    entry = (index.get("values", {}).get(key) or {}).get(lang)
    sheet = f"{lang}-{record['name']}"
    out = {"setup": setup, "call": call, "sheet": None, "file": None, "rect": None, "blank": False, "state": "missing", "note": None, "same": []}
    if entry is not None:
        out["state"] = "fresh" if entry.get("hash") == examples.value_hash(record["name"], name, value["value"], setup, call, lang) else "stale"
        out["blank"] = bool(entry.get("blank"))
        if entry.get("rect") and sheet in index.get("sheets", {}):
            out["sheet"], out["file"], out["rect"] = sheet, index["sheets"][sheet]["file"], list(entry["rect"])
        out["same"] = list(entry.get("same") or ())
    if name == "role" and record["name"] != "var-table":
        out["note"] = word("role_note", lang)
    elif out["same"]:
        out["note"] = word("same_as", lang, n=", ".join(out["same"]))
    return out


def value_bubble(record, name, lang, table=None, index=None):
    """The bubble of an argument's value (UI-007): the same head, then every value it takes -- what each does, the current one first lit -- and for each its call and its print; or, for an argument that takes free text, an example of one."""
    page = pages.entry(record["name"], table)
    spec = page["arguments"][name]
    default = default_of(record, name, spec)
    head = {"name": name, "status": status_text(record, name, spec, lang), "hover": word("values_hover", lang), "foot": word("frozen", lang)}
    if not spec.get("values"):
        example = next((tr(e["code"], lang) for e in spec["examples"] if tr(e["code"], lang)), "")
        return {**head, "values": [], "current": None, "free": {"text": word("free_text", lang), "example": example, "default": default}}
    index = examples.values_index() if index is None else index
    values = []
    for value in spec["values"]:
        values.append({"value": value["value"], "text": pages.value_text(value, lang, table), "preview": preview(record, name, value, lang, table, index)})
    current = next((v["value"] for v in values if default is not None and pages.bare(v["value"]) == pages.bare(str(default))), values[0]["value"])
    return {**head, "values": values, "current": current, "free": None}


# --- the list ------------------------------------------------------------------------------------------------

def lead(record, lang, table=None):
    """The one sentence the list shows under a command's name and the search reads: its page's lead, or -- for a command without a page yet -- the first sentence of its /// block in `lang`."""
    try:
        page = pages.entry(record["name"], table)
    except pages.PagesError:   # a malformed file: the page says it (commands_tab), the list keeps working on the /// block
        page = None
    if page is not None:
        return page["lead"][lang]
    paragraphs = record.get("paragraphs") or []
    return docs.prose(paragraphs[0], lambda code: code, lambda words: words, r"\1", r"\1") if paragraphs else ""


def matches(record, needle, lang, table=None):
    """Whether a search finds a command (REQ-011): in its name and in its lead, in the window's language -- never in its arguments or its values."""
    needle = needle.strip().lower()
    if not needle:
        return True
    return needle in record["name"].lower() or needle in lead(record, lang, table).lower()


# --- the examples --------------------------------------------------------------------------------------------

def levels_note(command, index, lang, manifest=None):
    """What an example whose levels print the same page says in place of its buttons (REQ-008): «Les trois niveaux impriment la même page.», «Les niveaux 2 et 3 …», or None."""
    same = examples.levels_same(command, index, manifest)
    return word(f"same{same}", lang) if same else None


def shown_levels(command, index, levels, manifest=None):
    """The levels an example's buttons offer (REQ-008, the prototype's rule): example_levels' three, and one alone -- the report's own -- where the three print the same page; two levels alike keep their buttons and are said (levels_note), the two showing the one page kept."""
    same = examples.levels_same(command, index, manifest)
    if same == "123" and len(levels) > 1:
        return (2,) if 2 in levels else tuple(levels[:1])
    return tuple(levels)


def calls(record, samples):
    """The two lines to copy (UI-010): command_docs.calls, the window's and the site's."""
    return docs.calls(record, samples)

