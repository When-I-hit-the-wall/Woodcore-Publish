"""How the «Formules» tab lays a domain out in its middle pane (issue #40, ARCH-004): the domain's items -- its commands and, between them, the engineer's own Typst -- as **paragraphs** of the pane, and back. Qt-free: the tab draws what this module says, and the round trip is tested without a window (tests/test_formula_domain.py).

**What the pane shows is what Typst prints** (the engineer, 11.10.2026: «si la commande autorise dans Typst l'affichage en ligne … cette commande doit également s'afficher en ligne dans le volet central»). The file keeps its form -- one command a line, the text between them as typed (formula_domain.body_of) --, and Typst reads a line break as a space: a text line, the line of a command printed inline and the next text line are **one sentence**. So the pane joins them into one paragraph, the command a pill in the middle; and a blank line between them, Typst's new paragraph, is where the pane breaks the line (D-05). Everything else stands as the file holds it, a line a paragraph: a text's own lines, a blank line between two of them, a command printed on a line of its own.

A paragraph is a list of runs, `("text", str)` or `("cmd", Command)`. A text run beside a pill carries the one space that parts them on screen; it is not written into the file.
"""

import re

import build_reference as ref
from domains import formula_domain as fd

INLINE, LINE = "inline", "line"


def placement(command):
    """INLINE where the command prints as a word of its sentence, LINE where it prints on a line of its own (REQ-002): every command of a domain written by hand prints inline since `note:` was retired -- a domain sets its lines apart with `#calc-defaults(presets: "block")`, Woodcore's own files do (spec 2026-10-21-commandes-typst-refonte, Q-014) -- so the pane joins it to its sentence."""
    return INLINE


# A line Typst never runs on into the line after it, nor the line before into it: a heading, a list's or a term's item (which would take the command into it), a comment.
_APART = re.compile(r"^\s*(=+\s|=+$|-\s|-$|\+\s|\+$|/\s|//)")


def joinable(line):
    """A text line a command printed inline may stand beside in one sentence: written, not a heading, a list's item or a comment, and closing what it opens -- an equation, a raw block, a string, a call (formula_domain.plain_spans: the line after it begins in plain markup)."""
    if not line.strip() or _APART.match(line):
        return False
    return len(line) + 1 in fd.plain_spans(line + "\n.")


def _joins(a, b, place):
    """Two tokens of the body -- a text line, or a command -- that Typst prints in one sentence, so the pane in one paragraph: a command inline beside a line that may stand beside it, or beside another command inline. Two text lines never: each is a paragraph of the pane, as the file has it."""
    if a is None or b is None or a == "" or b == "":
        return False
    a_cmd, b_cmd = not isinstance(a, str), not isinstance(b, str)
    if a_cmd and b_cmd:
        return place(a) == INLINE and place(b) == INLINE
    if a_cmd:
        return place(a) == INLINE and joinable(b)
    if b_cmd:
        return place(b) == INLINE and joinable(a)
    return False


def _tokens(items):
    """The body as a stream: each line of a text (a blank one as ""), each command as itself. An empty text -- a blank line between two commands (D-07) -- is one blank line. Also the indexes of the tokens the file writes on the line of the token before them: a command glued to what is beside it, and what follows a glued one (spec 2026-10-14-commandes-en-ligne-domaine, D-02)."""
    out, glued, prev = [], set(), None
    for c in items:
        if prev is not None and fd.same_line(prev, c):
            glued.add(len(out))
        if c.is_text:
            out.extend(c.raw.split("\n"))
        else:
            out.append(c)
        prev = c
    return out, glued


def _space(paragraph):
    """The one space a pill and the text beside it are parted by on screen; two pills side by side get a run of one space."""
    out = []
    for i, (kind, value) in enumerate(paragraph):
        before = paragraph[i - 1][0] if i > 0 else None
        if kind == "text":
            if before == "cmd":
                value = " " + value
            if i + 1 < len(paragraph) and paragraph[i + 1][0] == "cmd":
                value = value + " "
            out.append((kind, value))
        else:
            if before == "cmd":
                out.append(("text", " "))
            out.append((kind, value))
    return out


def to_paragraphs(items, place=placement):
    """The pane's paragraphs of the domain's items (formula_domain.tidy_items' form). A blank line between two tokens that would run into one sentence is the paragraph break between them and shows as no line of its own; any other blank line is an empty paragraph, as typed. A command written on one line with a text (D-02) -- `- $0°$: #var(…)`, which Typst keeps in the list's item -- is in that text's paragraph whatever `_joins` says."""
    tokens, glued = _tokens(fd.tidy_items(items))
    paragraphs, current = [], None
    for i, tok in enumerate(tokens):
        prev = tokens[i - 1] if i > 0 else None
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        if tok == "":
            if current is not None:
                paragraphs.append(current)
                current = None
            if not _joins(prev, nxt, place):
                paragraphs.append([])
            continue
        run = ("text", tok) if isinstance(tok, str) else ("cmd", tok)
        if current is not None and (i in glued or _joins(prev, tok, place)):
            current.append(run)
        else:
            if current is not None:
                paragraphs.append(current)
            current = [run]
    if current is not None:
        paragraphs.append(current)
    return [_space(p) for p in paragraphs]


def _unspaced(paragraph):
    """A paragraph's tokens as the file writes them: the space beside a pill taken off a text run, a run left empty by it dropped."""
    out = []
    for i, (kind, value) in enumerate(paragraph):
        if kind != "text":
            out.append(value)
            continue
        if i > 0 and paragraph[i - 1][0] == "cmd" and value.startswith(" "):
            value = value[1:]
        if i + 1 < len(paragraph) and paragraph[i + 1][0] == "cmd" and value.endswith(" "):
            value = value[:-1]
        if value or len(paragraph) == 1:
            out.append(value)
    return out


def from_paragraphs(paragraphs, place=placement):
    """The domain's items of the pane's paragraphs (formula_domain.tidy_items' form): each paragraph's runs in order, a text run a line, and, between two paragraphs whose ends Typst would run into one sentence, the blank line that keeps them apart -- the engineer's Enter beside a pill is a new paragraph in the report (D-05). Two runs in one paragraph that Typst would not join -- a heading and a pill, a command printed on a line of its own -- are written one after the other all the same: the pane shows them apart once it reads the file again (REQ-002). A command glued to what is beside it (D-02) stays glued while it stands inside its paragraph; at the paragraph's start or end it is glued to nothing on that side -- the flag set on the command itself, which the tab knows by its identity."""
    tokens = []
    for paragraph in paragraphs:
        part = _unspaced(paragraph)
        if not part or part == [""]:
            tokens.append("")
            continue
        if not isinstance(part[0], str):
            part[0].glued_before = False
        if not isinstance(part[-1], str):
            part[-1].glued_after = False
        if tokens and tokens[-1] != "" and _joins(tokens[-1], part[0], place):
            tokens.append("")
        tokens.extend(part)
    items, lines = [], None
    for tok in tokens:
        if isinstance(tok, str):
            lines = (lines or []) + [tok]
        else:
            if lines is not None:
                items.append(fd.Command(fd.TEXT, raw="\n".join(lines)))
                lines = None
            items.append(tok)
    if lines is not None:
        items.append(fd.Command(fd.TEXT, raw="\n".join(lines)))
    return fd.tidy_items(items)


def drop_refusal(paragraphs, at, place=placement):
    """Why a pill may not be dropped into paragraph `at[0]`, run `at[1]`, character `at[2]` of a text run -- None where it may (REQ-004, D-06). It may not where the command would change what the text around it means or stop the file from reading back: inside a heading (`= …` ends at its line, the command would leave it), a list's item, a comment, or inside an equation, a raw block, a string or a call that the line opens and has not closed there. Returns an English reason; the tab says its own words by `code`."""
    p, r, k = at
    paragraph = paragraphs[p] if 0 <= p < len(paragraphs) else []
    if not (0 <= r < len(paragraph)) or paragraph[r][0] != "text":
        return None
    text = paragraph[r][1]
    if _APART.match(text) and r == 0:
        return ("apart", "a command cannot stand inside a heading, a list's item or a comment: it would leave it once printed")
    head = text[:k]
    if len(head) + 1 not in fd.plain_spans(head + "\n."):
        return ("inside", "a command cannot stand inside an equation, a raw block, a string or a call: the domain would not read back")
    return None
