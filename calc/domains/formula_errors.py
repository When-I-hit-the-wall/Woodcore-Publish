"""Where a fault of a domain's file is, said as Typst says it (issue #113, spec docs/requirements/completed/2026-10-24-onglet-domaines-formulaire-code.md, REQ-007, D-14, ARCH-RISK-010).

**A file that does not read** -- a parenthesis forgotten -- is placed where Typst places it: at the **delimiter left open**, the innermost one still open at the end of the file, which is what `typst compile` names («error: unclosed delimiter», its line and its column). Not where Woodcore's own parser stumbled (the next command, lines below): the engineer looks for the parenthesis, not for the line after it. Found by typst_paths' lexer -- the one that walks Typst's modes --, without compiling (slow, and Typst may be missing); tests/test_formula_state.py holds it to `typst compile` where the binary is there. The column is the one Typst prints: the delimiter's offset in its line, in characters, from 0 (Typst 0.15 prints `#var(` at the start of a line as column 4).

**A line that does not compute** -- a name nobody declared, two dimensions added -- is a fault Typst names in the engine («while calling `get` at lib/formula.typ:1510»), never in the domain: the window says the line of the domain's file it is (`formula_rows.item_lines`), «ligne 13 de Domains/panne-p2.typ».

No Qt.
"""

import typst_objects


def read_fault(text):
    """{code, line, col} of what stops a domain's file from being read, as Typst places it -- `unclosed` (a parenthesis, a bracket, a brace left open), `string` (a string never closed), `raw` (a raw block never closed) -- or None where the lexer finds every delimiter closed. Lines from 1, the column from 0, as Typst prints them."""
    import typst_paths
    text = typst_objects._normalise(text)
    lexer = typst_paths._Lexer(text)
    opened = {}        # id of a frame of the stack -> where its delimiter is
    faults = []
    push, skip_string, raw, close = lexer._push, lexer._skip_string, lexer._raw, lexer._close

    def pushed(kind, closer=None, flag=0):
        push(kind, closer, flag)
        if closer in (")", "]", "}"):
            opened[id(lexer.stack[-1])] = lexer.i - 1

    def string(j):
        end = skip_string(j)
        if end >= lexer.n and not text.endswith('"'):
            faults.append(("string", j))
        return end

    def raw_block(j):
        end = raw(j)
        if end >= lexer.n and not text.rstrip().endswith("`"):
            faults.append(("raw", j))
        return end
    def closed(closer):
        # a closer that belongs to a frame further out ends the frames above it: a delimiter among them was left open -- what Typst says «unclosed delimiter» of (the `]` of `#domain(…)[` ends the `(` of a `#var(` whose `)` was forgotten)
        for depth in range(len(lexer.stack) - 1, 0, -1):
            if lexer.stack[depth][1] == closer:
                left = [opened[id(f)] for f in lexer.stack[depth + 1:] if id(f) in opened]
                if left:
                    faults.append(("unclosed", left[-1]))
                break
        close(closer)
    lexer._push, lexer._skip_string, lexer._raw, lexer._close = pushed, string, raw_block, closed
    while lexer.i < lexer.n:
        frame = lexer.stack[-1]
        at = lexer.i
        getattr(lexer, "_" + frame[0])(frame)
        if lexer.i == at and lexer.stack[-1] is frame:
            lexer.i += 1   # a lexer that does not move would loop: never seen, guarded
    if faults:
        code, where = faults[0]
    else:
        code = "unclosed"
        where = next((opened[id(f)] for f in reversed(lexer.stack) if id(f) in opened), None)
        if where is None:
            return None
    line = text.count("\n", 0, where) + 1
    col = where - (text.rfind("\n", 0, where) + 1)
    return {"code": code, "line": line, "col": col}


def where_text(here, domain, line):
    """«Domains/panne-p2.typ» and the line, what the window names a line of the domain by: (the file from the Typst root, line)."""
    path = domain.path
    rel = here.from_root(path).lstrip("/") if here is not None and path is not None else (path.name if path is not None else domain.id)
    return rel, line
