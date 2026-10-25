"""«Résultats» of a member check, a service (spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md, UI-011, REQ-014; issue #112).

The module the type's right pane shows under «Résultats» for a check, in its place (calc_modules.Modules takes a module «results» a service gives): **the verdict at its head** -- η in percent, ⩽ 100 %, ✔ green at 100 % or less, ✘ red above, no orange (CON-004) --, then **the rows in the order of the calculation**, η last, as `member_check.compute` gives them and the report prints them -- the symbol, the value and its unit, the clause at the right --; **the row that governs a maximum** (a side, an axis: `compute`'s `governing`) framed with a dashed line; a click on a row unfolds its formula. A row hovered lights the fields it is computed from (the context's `hover_result`). Nothing is computed or reordered here.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

import module_pane
import richtext
import theme
from tab_host import Hover, Service


def percent(value, lang):
    text = "%.1f" % (value * 100)
    return text.replace(".", ",") if lang in ("fr", "de") else text


def number(value, lang):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return str(value)
    magnitude = abs(value)
    text = ("%.0f" % value) if magnitude >= 1000 else ("%.3g" % value if magnitude < 0.01 and value else "%.3f" % value).rstrip("0").rstrip(".")
    return text.replace(".", ",") if lang in ("fr", "de") else text


class _ResultsBody(QWidget):
    """The verdict, then the rows -- see the module's docstring."""

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)
        self.verdict = QLabel("")
        self.verdict.setTextFormat(Qt.TextFormat.RichText)
        self.verdict.setWordWrap(True)
        column.addWidget(self.verdict)
        holder = QWidget()
        self.grid = QGridLayout(holder)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setHorizontalSpacing(6)
        self.grid.setVerticalSpacing(1)
        column.addWidget(holder)
        self.rows, self.open, self.lit, self.governing = {}, set(), set(), set()

    def refresh(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget() is not None:
                item.widget().hide()
                item.widget().deleteLater()
        self.rows = {}
        ctx, lang = self.ctx, self.ctx.app.lang
        instance = ctx.instance
        if instance is None:
            reason = next((ctx.message_text(m) for m in ctx.messages if m.severity == "error"), ctx.t("ct_none"))
            self.verdict.setText("<span style='color:%s'>%s</span>" % (theme.colour("muted"), richtext.escape(reason)))
            self.governing = set()
            return
        result = instance["result"]
        ok = result["ok"]
        colour = theme.colour("ok" if ok else "danger")
        self.verdict.setText("<b style='color:%s'>η = %s %% ⩽ 100 %% %s</b> &nbsp; <span style='color:%s'>%s</span>" % (
            colour, percent(result["eta"], lang), "✔" if ok else "✘", theme.colour("muted"), richtext.escape(ctx.t("vc_verdict_clause", clause=result["clause"], equation=result["equation"]))))
        self.governing = set(result.get("governing") or ())
        r = 0
        for row in result["rows"]:
            name = row["key"]
            value = percent(row["value"], lang) + " %" if name == "eta" else number(row["value"], lang) + ((" " + row["unit"]) if row.get("unit") else "")
            cite = " ".join(p for p in (row.get("norm") or "", row.get("clause") or "") if p) if row.get("clause") else ""
            cells = [(richtext.math_html(row["symbol"]), Qt.AlignmentFlag.AlignLeft), ("=", Qt.AlignmentFlag.AlignLeft),
                     (("<b>%s</b>" if name == "eta" else "%s") % richtext.escape(value), Qt.AlignmentFlag.AlignRight),
                     ("<span style='color:%s'>%s</span>" % (theme.colour("muted"), richtext.escape(cite)), Qt.AlignmentFlag.AlignRight)]
            labels = []
            for c, (text, align) in enumerate(cells):
                label = QLabel(text)
                label.setTextFormat(Qt.TextFormat.RichText)
                label.setAlignment(align | Qt.AlignmentFlag.AlignVCenter)
                label.setCursor(Qt.CursorShape.PointingHandCursor)
                label.installEventFilter(Hover(label, lambda n=name: self._enter(n), lambda: self._enter(None)))
                label.mousePressEvent = lambda _e, n=name: self.toggle(n)
                self.grid.addWidget(label, r, c)
                labels.append(label)
            self.rows[name] = labels
            r += 1
            if name in self.open and row.get("formula"):
                formula = QLabel("%s = %s" % (richtext.math_html(row["symbol"]), richtext.math_html(row["formula"])))
                formula.setTextFormat(Qt.TextFormat.RichText)
                formula.setWordWrap(True)
                formula.setStyleSheet("color: %s; padding-left: 12px;" % theme.colour("ink-soft"))
                self.grid.addWidget(formula, r, 0, 1, 4)
                r += 1
        self.grid.setColumnStretch(3, 1)
        self.set_lit(self.lit)
        self.setMinimumHeight(self.layout().sizeHint().height())   # a buckling's thirty rows: the pane scrolls, the rows are never squeezed

    def toggle(self, name):
        """A row clicked: its formula unfolded under it, or folded again."""
        self.open ^= {name}
        self.refresh()

    def _enter(self, name):
        self.ctx.hover_result(name)

    def set_lit(self, names):
        """The rows `names` on the theme's `hover` ground; the governing row framed with a dashed line (REQ-014)."""
        self.lit = set(names or ())
        lit = "background: %s; color: %s;" % (theme.colour("hover"), theme.colour("hover-ink"))
        frame = "border-top: 1px dashed %s; border-bottom: 1px dashed %s;" % (theme.colour("ink"), theme.colour("ink"))
        for name, labels in self.rows.items():
            for label in labels:
                label.setStyleSheet((lit if name in self.lit else "") + (frame if name in self.governing else ""))

    def framed(self):
        """The names of the rows framed with a dashed line -- what a test reads."""
        return set(n for n in self.rows if n in self.governing)

    def text(self):
        cells = " ".join(self.grid.itemAt(i).widget().text() for i in range(self.grid.count()))
        return (self.verdict.text() + " " + cells).strip()

    def order(self):
        """The names of the rows in the order they are shown."""
        return list(self.rows)


class CheckResults(Service):
    """The module «Résultats» of a member check -- see the module's docstring. No pane of its own: it gives the type's right pane its module, in place of the type's «Résultats»."""

    NAME = "check_results"
    NEEDS = ("build_instance",)

    def mount(self, ctx):
        super().mount(ctx)
        ctx.pane_modules.append(module_pane.ModuleSpec("results", self.t("ct_module_results"), lambda: _ResultsBody(ctx), kind="results"))
        return None
