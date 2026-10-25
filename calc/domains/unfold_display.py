"""«Affichage» of a domain's file: its elements, and what the engineer sets of them (spec 2026-10-22-onglet-neige-type, REQ-011 to REQ-014, REQ-016, UI-012, D-17, D-23, D-29, D-30).

Written beside calc/domains/unfold.py and on it -- the file's lines, their base, the targeted write every operation of unfold uses (`unfold._write`: only what changed, the file checked unchanged first) --, never imported by it: unfold writes the domains, this module reads them for the window and writes what «Affichage» sets. Qt-free; calc/tools/domain_file_display.py draws it.
"""

import re

import line_display
from domains import unfold


# # The view lists every element of the file -- the domain's header, a figure, each `#var`, `#eq`, `#verify` -- and writes what the engineer sets into the file at once, by the targeted write every operation of this module uses (`_write`: only what changed, the file checked unchanged first, the base beside it). The base is not touched: an argument of a line's display is no change of it (D-17), a label or a formula typed here makes the line the engineer's (`local`), which no export writes over. Qt-free; calc/tools/domain_file_display.py draws it.

# What «Affichage» may write on a line beyond its display (T63, T64): an `#eq`'s formula, units, label and description, a `#verify`'s label -- each makes the line the engineer's own
WRITABLE = {"var": (), "eq": ("equation", "unit", "as-unit", "label", "descr"), "verify": ("label",)}
_HEADER = re.compile(r"^(\s*#domain\(.*)\)\[\s*$")
_LEVEL = re.compile(r",\s*level:\s*[^,)]+")
# A figure's line as `figure_line` writes it, commented out or not, printed from a level on or not (`#from-level(3)[…]`, D-29 of spec 2026-10-23-onglet-vent-briques): what «Affichage» reads and writes again
_FIGURE = re.compile(r'^(?P<mask>//\s*)?(?:#from-level\((?P<level>\d)\)\[)?#figure\(image\("(?P<file>[^"]+)", width: (?P<width>[^)]+)\)(?:, caption: \[(?P<caption>.*)\])?\) <(?P<label>[A-Za-z0-9_.:-]+)>(?(level)\])$')
# A table's lines as unfold._table_lines labels them: the table, its title, its note
_TABLE = re.compile(r"^label:(?P<rid>.+)-table-(?P<i>\d+)(?P<part>-title|-note)?$")


def _header_line(text):
    """(index, line) of the domain's header `#domain(…)[` in the file's lines, or (None, None)."""
    for i, line in enumerate(text.split("\n")):
        if _HEADER.match(line):
            return i, line
    return None, None


def is_table_line(line, rid):
    """Whether `line` is one of the lines of a table of the domain `rid` -- the table, its title, its note."""
    return any(_TABLE.match(lid) and _TABLE.match(lid).group("rid") == rid for lid, _l in unfold.text_lines(line))


def case_file(here, rid, kind):
    """The file of the case `rid` of `kind` that «Affichage» shows, or None where it is not written -- none in a project laid out before the folders of v0.119, nor for a kind with no folder of its own: the one rule of the view's that is no widget's (spec 2026-10-23-onglets-types-et-services, ARCH-005)."""
    if here is None or not rid or here.domain_dir(kind) is None:
        return None
    found = unfold.domain_path(here, rid, kind=kind)
    return found if found.is_file() else None


def domain_level(text):
    """The level the domain's header gives its lines (`#domain(…, level: n)`), None where it leaves it to the report (D-30: «auto»)."""
    _i, line = _header_line(text)
    found = re.search(r"level:\s*(\d)", line or "")
    return int(found.group(1)) if found else None


def figure_parts(line):
    """{file, width, caption, label, masked, level} of a figure's line as `figure_line` writes it, commented out or not (D-23), `level` the one it is printed from (None: every level); {} for a line written another way -- the engineer's form, set in VS Code."""
    found = _FIGURE.match(line.strip())
    if not found:
        return {}
    return {"file": found.group("file"), "width": found.group("width"), "caption": found.group("caption") or "",
            "label": found.group("label"), "masked": bool(found.group("mask")), "level": int(found.group("level")) if found.group("level") else None}


def elements(here, rid, kind):
    """Every element of the file of the domain `rid` of `kind`, in its order, as «Affichage» lists them (UI-012): the header {id: "domain", level}, each figure {id: "figure:<file>", width, caption, label, masked, level, line}, each table {id: "table:<i>", kind: "table", label (its title), shown, title, note -- each shown, or None where it has none --, line} (spec 2026-10-23-onglet-vent-briques, UI-024: no level), each command Woodcore finds a line by {id: "<kind>:<name>", kind, key, symbol, label, level, options, line} -- `options` the arguments of its display it writes, `line` its call as the file holds it. A line of the engineer's own text is no element."""
    from domains import formula_domain as fd
    domain = unfold._read_domain(here, rid, kind)
    out = [{"id": "domain", "kind": "domain", "level": domain_level(domain.text)}]
    tables = {}
    for c in domain.commands:
        if c.is_text:
            for line_id, line in unfold.text_lines(c.raw):
                if line_id.startswith("figure:"):
                    out.append(dict({"id": line_id, "kind": "figure", "line": line.strip()}, **figure_parts(line)))
                    continue
                found = _TABLE.match(line_id)
                if not found or found.group("rid") != rid:
                    continue
                i = found.group("i")
                if i not in tables:
                    tables[i] = {"id": "table:" + i, "kind": "table", "label": "", "shown": None, "title": None, "note": None, "line": ""}
                    out.append(tables[i])
                part = (found.group("part") or "-table")[1:]
                tables[i]["shown" if part == "table" else part] = not unfold.is_masked(line)
                if part == "table":
                    tables[i]["line"] = line.strip()
                elif part == "title":
                    tables[i]["label"] = re.sub(r"\s*<[^>]+>$", "", unfold.unmasked(line)).strip("_ ")
            continue
        name = unfold.line_name(c, unfold._legacy(domain))
        if not name or c.kind not in ("var", "eq", "verify"):
            continue
        shown = {k: v for k, v in c.options.items() if k in line_display.display_args(c.kind)}
        out.append({"id": f"{c.kind}:{name}", "kind": c.kind, "key": c.key, "symbol": c.symbol or c.key, "label": c.options.get("label") or "",
                    "level": c.options.get("level"), "options": shown, "line": (c.written or "  " + fd.to_call(c)).strip()})
    return out


def _write_lines(here, rid, kind, change):
    """The file of `rid` written with `change(domain, items)` -> items, its base entry as it stands: an operation of «Affichage»."""
    domain = unfold._read_domain(here, rid, kind)
    record = unfold._record_of(here, rid, kind)
    base = unfold.read_base(here, kind)
    entry = unfold._entry(record, base, rid, kind) if record is not None else base["domains"].get(rid, {"check": rid, "gen": None, "lines": {}})
    items = change(domain, list(domain.commands))
    return unfold._write(here, domain, items, base, rid, entry, kind=kind)


def set_display(here, rid, line_id, values, kind):
    """The arguments `values` {name: value, or None to take it away} set on the line `line_id` of the domain `rid` (REQ-013): those of its display (calc/line_display.py) and, for an `#eq` or a `#verify`, what `WRITABLE` names; any other name is refused. Written into the file at once, the rest of the line as it stands."""
    from domains import formula_domain as fd
    command = line_id.partition(":")[0]
    allowed = set(line_display.display_args(command)) | set(WRITABLE.get(command, ()))
    wrong = sorted(set(values) - allowed)
    if wrong:
        raise unfold.UnfoldError(f"unfold: {', '.join(wrong)} is not set on a #{command} in «Affichage» -- {', '.join(sorted(allowed))}", "not_writable", line=line_id)

    def change(domain, items):
        held = unfold._items_by_line(items, unfold._legacy(domain)).get(line_id)
        if held is None or held[1].is_text:
            raise unfold.UnfoldError(f"unfold: {rid} holds no line {line_id!r}", "no_line", id=rid, line=line_id)
        index, c = held
        options = dict(c.options)
        formula, unit = c.formula, c.unit
        for name, value in values.items():
            if name == "equation":
                formula = value if value else c.formula
            elif name == "unit" and command == "eq":
                unit = value or ""
            elif value is None:
                options.pop(name, None)
            else:
                options[name] = value
        items[index] = fd.replace(c, options=options, formula=formula, unit=unit)
        return items
    return _write_lines(here, rid, kind, change)


def set_figure(here, rid, line_id, width=None, caption=None, label=None, shown=None):
    """A figure's line set (REQ-016, T65): its width, its caption, its label -- the line stays Woodcore's, found by its image (D-29) --, and masked or shown, its line commented out or back (D-23). None leaves a part as it is."""
    kind = unfold.kind_of(here, rid)

    def change(domain, items):
        for index, c in enumerate(items):
            if not c.is_text or not any(lid == line_id for lid, _l in unfold.text_lines(c.raw)):
                continue
            lines = c.raw.split("\n")
            for i, line in enumerate(lines):
                if not any(lid == line_id for lid, _l in unfold.text_lines(line)):
                    continue
                parts = figure_parts(line)
                if not parts:
                    raise unfold.UnfoldError(f"unfold: the figure {line_id!r} of {rid} is written in a form of the engineer's own -- set it in VS Code", "figure_own", id=rid, line=line_id)
                lead = line[:len(line) - len(line.lstrip())]
                new = unfold.figure_line(parts["file"], caption or "", parts["label"] if label is None else re.sub(r"[^A-Za-z0-9_.:-]", "-", label),
                                  parts["width"] if width is None else width, written=parts["caption"] if caption is None else None, level=parts["level"])
                masked = parts["masked"] if shown is None else not shown
                lines[i] = lead + ("// " if masked else "") + new
            from domains import formula_domain as fd
            items[index] = fd.Command(c.kind, raw="\n".join(lines))
            return items
        raise unfold.UnfoldError(f"unfold: {rid} holds no figure {line_id!r}", "no_line", id=rid, line=line_id)
    return _write_lines(here, rid, kind, change)


def set_table(here, rid, number, kind, shown=None, title=None, note=None):
    """A table of the file shown or masked, with or without its title and its note (UI-024, ARCH-008): each of its lines commented out or back, the rest of the line as it stands. None leaves a part as it is; a part the table does not have is refused."""
    wanted = {"": shown, "-title": title, "-note": note}
    ids = {"label:%s-table-%s%s" % (rid, number, part): on for part, on in wanted.items() if on is not None}

    def change(domain, items):
        found = set()
        for index, c in enumerate(items):
            if not c.is_text:
                continue
            lines = c.raw.split("\n")
            touched = False
            for i, line in enumerate(lines):
                for lid, _l in unfold.text_lines(line):
                    if lid in ids:
                        lead = line[:len(line) - len(line.lstrip())]
                        lines[i] = lead + ("" if ids[lid] else "// ") + unfold.unmasked(line)
                        found.add(lid)
                        touched = True
            if touched:
                from domains import formula_domain as fd
                items[index] = fd.Command(c.kind, raw="\n".join(lines))
        missing = sorted(set(ids) - found)
        if missing:
            raise unfold.UnfoldError(f"unfold: {rid} holds no line {', '.join(missing)}", "no_line", id=rid, line=missing[0])
        return items
    return _write_lines(here, rid, kind, change)


_DESCR = re.compile(r',\s*descr:\s*"(?:[^"\\]|\\.)*"')
_LABEL_POSITION = re.compile(r',\s*label-position:\s*"[^"]*"')
_TITLE = re.compile(r'label:\s*"(?:[^"\\]|\\.)*"')


def apply_check_display(here, rid, record, retitle=False):
    """The options of «Affichage» a member check keeps in its **source** (issue #112, REQ-010, ARCH-005, ARCH-010) written onto its file after an export: the header's `descr:`, `label-position:` and `level:` as `unfold.check_header` writes them -- every other argument of the header as it stands --, and the member's line masked (`// `) where the source says «none», shown again where it says otherwise. The source is the one store of a check's display: what the file held of these is written over, never read back (`_with_display` reports no argument of the file onto a check). A record without `display` leaves the file's member line as it is. Returns whether the file was written."""
    import sharing
    from domains import formula_domain as fd, member_check_material
    path = case_file(here, rid, "check")
    if path is None or not unfold.is_domain_file(path):
        return False
    display = member_check_material.display_of(record)
    domain = unfold._read_domain(here, rid, "check")
    text = domain.text
    lines = text.split("\n")
    index, line = _header_line(text)
    if index is not None:
        head = _HEADER.match(line).group(1)
        for pattern in (_DESCR, _LABEL_POSITION, _LEVEL):
            head = pattern.sub("", head)
        if retitle:
            # the kind changed (REQ-011): the title of the new form
            import build_reference as ref
            import positions_store
            head = _TITLE.sub(lambda m: "label: " + ref.typst_str(unfold.check_title(record, positions_store.project_language(here))), head, count=1)
        fresh = unfold.check_header(rid, "", record, display)
        extra = fresh[fresh.index('label: ""') + len('label: ""'):-2]   # what the options add after the title
        lines[index] = head + extra + ")[" + line[len(line.rstrip("\r")):]   # a file written with CRLF keeps its line ending
    if "display" in record:
        member_id = unfold._label(rid, "member")
        for i, l in enumerate(lines):
            if member_id in l and not l.lstrip().startswith("#domain("):
                lead = l[:len(l) - len(l.lstrip())]
                masked = display["member_line"] == "none"
                lines[i] = lead + ("// " if masked else "") + unfold.unmasked(l)
                break
    new = "\n".join(lines)
    if new == text:
        return False
    fd.check_unchanged(domain)
    sharing._commit([(domain.path, new.encode("utf-8"), text.encode("utf-8"))])
    return True


def set_domain_level(here, rid, level, kind):
    """The level of the domain's lines, `#domain(…, level: n)` (REQ-011): 1, 2 or 3, or None to leave it to the report (D-30). Only the header's `level:` is written -- everything else of the header, written by hand or not, as it stands (ARCH-RISK-F12)."""
    import sharing
    from domains import formula_domain as fd
    if level not in (None, 1, 2, 3):
        raise unfold.UnfoldError(f"unfold: level {level!r} -- 1, 2, 3 or none", "bad_level", level=level)
    domain = unfold._read_domain(here, rid, kind)
    fd.check_unchanged(domain)
    lines = domain.text.split("\n")
    index, line = _header_line(domain.text)
    if index is None:
        raise unfold.UnfoldError(f"unfold: {rid} has no #domain header", "no_header", id=rid)
    head = _HEADER.match(line).group(1)
    head = _LEVEL.sub("", head)
    lines[index] = head + (f", level: {level}" if level is not None else "") + ")["
    text = "\n".join(lines)
    sharing._commit([(domain.path, text.encode("utf-8"), domain.text.encode("utf-8"))])
    return text
