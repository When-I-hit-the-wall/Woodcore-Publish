"""A symbol written in Typst's math source -- `q_(k,"max")`, `(g_k + a_k)_"gew"`, `f_(h,alpha,k)` -- read once and set two ways (spec docs/requirements/completed/2026-10-11-variables-liees-champs-et-textes.md, ARCH-006):

- `to_html(source)`: as HTML Qt's rich text sets it, q<sub>k,max</sub>, the Greek names as Greek letters, `dot` as · -- what `richtext.math_html` has set the window's symbols with since v0.92, moved here unchanged so that a figure can read the same symbol;
- `to_figure(source)`: in the dialect a figure's text is cut by (`svg_text.text_runs`): `q_(k,max)`, a subscript after an underscore and in brackets, the Greek letters as letters, the quotes taken off -- what a text of a drawing prints a variable's symbol with («symbole = valeur», D-09).

One reader, two writers: a symbol is never read one way in the window and another on the figure. No Qt.
"""

import greek

# the Greek names Typst's math knows, and their letters: calc/greek.py's, which is formula.typ's own list (v0.117)
GREEK = greek.LETTERS
MATH_WORDS = {"dot": " · ", "times": " × ", "space": " ", "thin": " ", "quad": "  ", "minus": "−", "infinity": "∞"}


def escape(text):
    """A value the data carries, escaped before it goes into rich text."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render(source, html):
    text = str(source)
    esc = escape if html else (lambda value: str(value))

    def atom(i):
        # one token: (text, next index)
        if i >= len(text):
            return "", i
        ch = text[i]
        if ch == '"':
            j = text.find('"', i + 1)
            j = len(text) if j < 0 else j
            return esc(text[i + 1:j]), j + 1
        if ch.isalpha():
            j = i
            while j < len(text) and text[j].isalpha():
                j += 1
            word = text[i:j]
            return GREEK.get(word, MATH_WORDS.get(word, esc(word))), j
        if ch.isdigit() or ch == ".":
            j = i
            while j < len(text) and (text[j].isdigit() or text[j] == "."):
                j += 1
            return text[i:j], j
        if ch == "(":
            inner, j = sequence(i + 1, ")")
            return "(%s)" % inner, j + 1
        if text.startswith("\\/", i):
            return "/", i + 2
        if text.startswith("<=", i):
            return " ≤ ", i + 2
        if text.startswith(">=", i):
            return " ≥ ", i + 2
        return esc(ch), i + 1

    def sequence(i, stop=None):
        out = []
        while i < len(text) and (stop is None or text[i] != stop):
            if text[i].isspace():
                if out and not out[-1].endswith(" "):
                    out.append(" ")
                i += 1
                continue
            piece, i = atom(i)
            if piece.startswith(" ") and out and out[-1].endswith(" "):
                piece = piece.lstrip()   # `a dot b`: the space typed and the one `·` is set with are one
            while i < len(text) and text[i] in "_^":
                sub = text[i] == "_"
                if i + 1 < len(text) and text[i + 1] == "(":
                    script, i = sequence(i + 2, ")")
                    i += 1
                else:
                    script, i = atom(i + 1)
                script = script.strip()
                if html:
                    tag = "sub" if sub else "sup"
                    piece += "<%s>%s</%s>" % (tag, script, tag)
                else:
                    # a figure sets a subscript after an underscore, in brackets where it is more than one letter or digit (svg_text.SUBSCRIPT); it has no superscript, which is written as it reads
                    piece += ("_(%s)" % script) if sub else ("^" + script)
            out.append(piece)
        return "".join(out), i

    return sequence(0)[0].strip()


def to_html(source):
    """`K_("ser","Verb")` as K<sub>ser,Verb</sub>, `k_(beta,1)` as k<sub>β,1</sub>, `7 d` as 7 d."""
    return _render(source, html=True)


def to_figure(source):
    """`K_("ser","Verb")` as `K_(ser,Verb)`, `k_(beta,1)` as `k_(β,1)`, `"Kategorie"` as `Kategorie` -- a figure's text cuts it as the window shows it."""
    return _render(source, html=False)
