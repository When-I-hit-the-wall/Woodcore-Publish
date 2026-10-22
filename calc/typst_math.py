"""A symbol written in Typst's math source -- `q_(k,"max")`, `(g_k + a_k)_"gew"`, `f_(h,alpha,k)` -- read once and set two ways (spec docs/requirements/completed/2026-10-11-variables-liees-champs-et-textes.md, ARCH-006):

- `to_html(source)`: as HTML Qt's rich text sets it, q<sub>k,max</sub>, the Greek names as Greek letters, `dot` as · -- what `richtext.math_html` has set the window's symbols with since v0.92, moved here unchanged so that a figure can read the same symbol;
- `to_figure(source)`: in the dialect a figure's text is cut by (`svg_text.text_runs`): `q_(k,max)`, a subscript after an underscore and in brackets, the Greek letters as letters, the quotes taken off -- what a text of a drawing prints a variable's symbol with («symbole = valeur», D-09).

One reader, two writers: a symbol is never read one way in the window and another on the figure. No Qt.

- `normalise(source)`: every subscript written as the report prints it -- lib/subscript.typ's `normalize-subscripts`, its Python twin (spec docs/requirements/completed/2026-10-20-indices-et-niveaux.md, UI-001, ARCH-001): a subscript of letters, digits, Greek names, commas and spaces is one quoted block, `N_(R d)` → `N_"Rd"`, `gamma_(M 1)` → `gamma_"M1"`, `f_(c,alpha,d)` → `f_"c,α,d"`; one of digits, the bound of an operator, quoted text and code are left alone. Both writers above read the source through it, so the window, a figure and the page write the same subscript. tests/test_subscripts.py holds it equal to Typst's on every symbol and formula of the domains, of lib/ and of the example's export.
"""

import re

import greek

# the Greek names Typst's math knows, and their letters: calc/greek.py's, which is formula.typ's own list (v0.117)
GREEK = greek.LETTERS
MATH_WORDS = {"dot": " · ", "times": " × ", "space": " ", "thin": " ", "quad": "  ", "minus": "−", "infinity": "∞"}


# lib/subscript.typ's pattern, written with the same regex in both engines (Rust's and Python's read it alike): a quoted span, an escape, `#` code's name, an operator with its bound -- all four copied as they stand --, a subscript in brackets (group 1), a subscript of one name (group 2)
LIMITS = ("sum", "product", "integral", "lim", "limsup", "liminf", "max", "min", "sup", "inf")
# a name's characters: letters, marks, digits -- not the superscript and subscript digits (², ₁), which Python's \w takes and Rust's leaves out: written out, so both engines read the same
_NAME = r'[^\W_²³¹¼½¾⁰-₟]'
_QUOTED = r'"(?:[^"\\]|\\.)*"'
_SUBSCRIPT = re.compile(
    _QUOTED + r'|\\.|#[^\W\d][\w.-]*'
    + r'|\b(?:' + "|".join(LIMITS) + r')_(?:\([^()]*\)|' + _NAME + r'+)'
    + r'|_\(((?:[^()"]|' + _QUOTED + r')*)\)'
    + r'|_(' + _NAME + r'+)')
_SIMPLE = re.compile(r'^(?:' + _NAME + r'|[ ,]|' + _QUOTED + r')*$')
_PIECE = re.compile(_QUOTED + r'|' + _NAME + r'+|,')
_LETTER = re.compile(r'[^\W\d_²³¹¼½¾⁰-₟]')


def _block(content):
    """The quoted block a simple subscript is written as: its parts joined by tight commas, a quoted span's text as it is, a Greek name as its letter, spaces dropped (`R d` is `Rd`)."""
    out = ""
    for m in _PIECE.finditer(content):
        t = m.group(0)
        out += "," if t == "," else t[1:-1] if t.startswith('"') else GREEK.get(t, t)
    return '"' + out + '"'


def _rewrite(m):
    group, name = m.group(1), m.group(2)
    if group is not None:
        if not _SIMPLE.match(group) or not _LETTER.search(group.replace('"', "")):
            return m.group(0)
        return "_" + _block(group)
    if name is not None:
        return m.group(0) if re.fullmatch(r"\d+", name) else "_" + _block(name)
    return m.group(0)


def normalise(source):
    """`source` with every subscript written as the report prints it (lib/subscript.typ, `normalize-subscripts`): `M_(y,R d) = f_y dot W_(p l,y) / gamma_(M 1)` → `M_"y,Rd" = f_"y" dot W_"pl,y" / gamma_"M1"`; `sum_(i=1)^n`, `mu_11` and quoted text unchanged. Applying it twice changes nothing."""
    text = str(source)
    if "_" not in text:
        return text
    return _SUBSCRIPT.sub(_rewrite, text)


def escape(text):
    """A value the data carries, escaped before it goes into rich text."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _render(source, html):
    text = normalise(source)
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
