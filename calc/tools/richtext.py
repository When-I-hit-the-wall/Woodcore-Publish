"""What the window sets as rich text rather than as plain words (docs/ui/window.md §10quater, v0.92): a symbol of the data as mathematics, a Typst call coloured the way the website colours its code, and the field and the button a call is copied with.

- `math_html(source)`: a symbol written in Typst's math source -- `q_(k,"max","b·h")`, `(g_k + a_k)_"gew"`, `f_(h,alpha,k)` -- as HTML Qt's rich text sets: q<sub>k,max,b·h</sub>, the Greek names as Greek letters, `dot` as ·. `prose_html(sentence)` sets a sentence's symbols between dollars the same way, render-prose's rule in lib/calc-engine.typ.
- `typst_html(code)`: a Typst call coloured by the site's own syntax tokens (theme.json's `syn-*`): comments, strings, raw blocks, math, keywords, calls, named arguments, numbers. The tokeniser is typst_syntax.py's, which the website's build imports too.
- `CodeField`, the call as the site sets a code block -- the site's code ground and font, the call coloured -- and `copy_button`, which says «Copié ✓» for a moment once it has copied, as the site's copy button does. `TypstHighlighter` colours an example of several lines in a `QPlainTextEdit` the same way, and `MathDelegate` sets a column of symbols as mathematics.

`math_html`, `prose_html`, `subscripts`, `results_html` and `typst_html` are plain text in, HTML out; the rest are Qt's. The colours are read from theme.py when a widget is built, and a scheme changed builds the window again (woodcore_gui.retheme).
"""

import html
import re

from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QAbstractTextDocumentLayout, QColor, QFont, QPalette, QSyntaxHighlighter, QTextCharFormat, QTextDocument
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QSizePolicy, QStyle, QStyledItemDelegate, QStyleOptionViewItem

import theme
import typst_syntax  # the tokeniser the website sets its code with (v0.92)

# --- symbols -----------------------------------------------------------------------------------------------------

# The reading of a symbol is calc/typst_math.py's since issue #43, where a figure's text reads it too (ARCH-006): moved there unchanged, every name still importable from here.
import typst_math  # noqa: E402
GREEK = typst_math.GREEK
MATH_WORDS = typst_math.MATH_WORDS
escape = typst_math.escape


def math_html(source):
    """`K_("ser","Verb")` as K<sub>ser,Verb</sub>, `k_(beta,1)` as k<sub>β,1</sub>, `7 d` as 7 d -- what the connectors tab set its results with since v0.70, shared here since v0.92 (typst_math.to_html)."""
    return typst_math.to_html(source)


def prose_html(sentence):
    """A sentence the data carries, its symbols between dollars set as `math_html` sets them and its words escaped -- render-prose's rule in lib/calc-engine.typ, an unpaired dollar leaving the sentence as it is."""
    parts = str(sentence).split("$")
    if len(parts) % 2 == 0:
        return escape(sentence)
    return "".join(math_html(p) if i % 2 else escape(p) for i, p in enumerate(parts))


SUBSCRIPT = re.compile(r"(?<![\w&])([A-Za-zα-ωΑ-Ω])_(\([^)]*\)|[\w,]+)")


def subscripts(text):
    """A line of the window's own words whose symbols are written `F_max`, `I_p,x`: escaped, each `x_…` set with its subscript, the lines kept -- for a sentence that is mostly words, where `math_html` would read every word as a symbol."""
    lines = []
    for line in str(text).split("\n"):
        escaped = escape(line)
        lines.append(SUBSCRIPT.sub(lambda m: f"{m.group(1)}<sub>{m.group(2).strip('()')}</sub>", escaped))
    return "<br>".join(lines)


def results_html(rows):
    """Results as the connectors tab sets them: one row each, the symbol as mathematics, `=`, the value right-aligned; `rows` is [(symbol source, value text, bold), ...]."""
    body = []
    for symbol, value, bold in rows:
        weight = "font-weight:600;" if bold else ""
        body.append(f'<tr><td style="padding-right:8px;{weight}">{math_html(symbol)}</td><td style="padding-right:6px">=</td>'
                    f'<td align="right" style="{weight}">{escape(value)}</td></tr>')
    return '<table cellspacing="0" cellpadding="1">' + "".join(body) + "</table>"


# --- Typst, coloured ---------------------------------------------------------------------------------------------

# The tokeniser is typst_syntax.py's, the one the website sets its code with; the colours are theme.json's syn-* tokens.
TYPST_TOKEN = typst_syntax.TYPST_TOKEN
SYNTAX = typst_syntax.THEME_TOKEN


def typst_html(code):
    """A Typst call as rich text, coloured in the scheme in force by the site's syntax tokens; the keywords bold and the comments italic, as the site sets them."""
    out, pos = [], 0
    for m in TYPST_TOKEN.finditer(code):
        out.append(html.escape(code[pos:m.start()], quote=False))
        kind = m.lastgroup
        style = f"color:{theme.colour(SYNTAX[kind])}"
        if kind == "keyword":
            style += "; font-weight:600"
        elif kind == "comment":
            style += "; font-style:italic"
        out.append(f'<span style="{style}">{html.escape(m.group(), quote=False)}</span>')
        pos = m.end()
    out.append(html.escape(code[pos:], quote=False))
    return "".join(out)


class TypstHighlighter(QSyntaxHighlighter):
    """The same colours on a `QPlainTextEdit` of several lines -- a worked example of the commands tab, which stays selectable and scrollable as it was. Line by line, so a `/* … */` comment spanning lines is coloured on its first line only; no example of lib/ writes one."""

    def highlightBlock(self, text):
        for m in TYPST_TOKEN.finditer(text):
            kind = m.lastgroup
            form = QTextCharFormat()
            form.setForeground(QColor(theme.colour(SYNTAX[kind])))
            if kind == "keyword":
                form.setFontWeight(QFont.Weight.DemiBold)
            elif kind == "comment":
                form.setFontItalic(True)
            self.setFormat(m.start(), m.end() - m.start(), form)


# --- the widgets -------------------------------------------------------------------------------------------------

class CodeField(QLabel):
    """A Typst call as the site sets a code block: its code ground, a thin line round it (`QLabel#code` in theme.py), the call coloured and selectable, on one line, clipped rather than widening its pane -- the whole call in its tooltip and on the clipboard. `text()` gives the call as it is copied, as the QLineEdit it replaced did."""

    def __init__(self, code, font):
        super().__init__()
        self.code = code
        self.setObjectName("code")
        self.setFont(font)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setWordWrap(False)
        self.setToolTip(code)
        super().setText(f'<span style="white-space:pre">{typst_html(code)}</span>')

    def text(self):
        return self.code


def copy_button(label, done, copy):
    """The button beside a call: `copy()` on a click, then «Copié ✓» (`done`) for a moment on the accent's ground, as the site's copy button says it -- the status line said it too far from the pointer."""
    button = QPushButton(label)
    button.setMinimumWidth(button.fontMetrics().horizontalAdvance(max(label, done, key=len)) + 28)

    def mark(on):
        button.setText(done if on else label)
        button.setProperty("done", on)
        button.style().unpolish(button)
        button.style().polish(button)

    def back():
        try:
            mark(False)
        except RuntimeError:
            pass   # the button went with a rebuilt pane meanwhile

    def clicked(_checked=False):
        copy()
        mark(True)
        QTimer.singleShot(1400, back)

    button.clicked.connect(clicked)
    return button


class MathDelegate(QStyledItemDelegate):
    """Sets the item text of `columns` as mathematics (`math_html`) and every other column as it was: the loads tree's Symbole column showed Typst's source -- `q_(k,"max","b·h")` -- where it shows q with its subscript since v0.92."""

    def __init__(self, parent, columns):
        super().__init__(parent)
        self.columns = set(columns)

    def _document(self, font, source):
        doc = QTextDocument()
        doc.setDefaultFont(font)
        doc.setDocumentMargin(0)
        doc.setHtml(math_html(source))
        return doc

    def paint(self, painter, option, index):
        if index.column() not in self.columns:
            return super().paint(painter, option, index)
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        source = opt.text
        opt.text = ""
        widget = opt.widget
        (widget.style() if widget is not None else QApplication.style()).drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, widget)
        doc = self._document(opt.font, source)
        painter.save()
        rect = opt.rect.adjusted(4, 0, -2, 0)
        painter.translate(rect.left(), rect.top() + max(0.0, (rect.height() - doc.size().height()) / 2))
        painter.setClipRect(QRectF(0, -rect.height(), rect.width(), rect.height() * 3))
        context = QAbstractTextDocumentLayout.PaintContext()
        # the ink of every row, a selected one included: an item view selects on accent-soft with the ordinary ink (theme.py's QAbstractItemView::item:selected)
        context.palette.setColor(QPalette.ColorRole.Text, QColor(theme.colour("ink")))
        doc.documentLayout().draw(painter, context)
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if index.column() in self.columns:
            size.setWidth(int(self._document(option.font, index.data(Qt.ItemDataRole.DisplayRole) or "").idealWidth()) + 8)
        return size
