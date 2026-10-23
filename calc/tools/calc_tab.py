"""The common base of the calculation tabs: a tab described by its domain, never copied (spec 2026-10-22-onglet-neige-type, ARCH-001, ARCH-002, ARCH-003, D-1, D-2, D-25; docs/ui/calc-tab.md).

**What a tab of calculation is made of.** `LoadTab` (load_tab.py) gives it what every editor tab has -- the list of the cases in folders with «Archives», «Nouveau» · «Dupliquer» · «Supprimer», Nom · Description · ID, «Enregistrer», the views «Calcul» and «Affichage», a field linked to a variable. **`DeclaredTabMixin`** gives it the rest from its domain's declaration (calc/domains/contracts.py `CalcTabDomain`): the form in sections, each datum with its ⓘ (calc_fields, norm_bubble), and the right pane of modules (module_pane) -- the state of the calculation in red, orange and green, the results, the domain's drawing and chart where it has them, and the excerpts of the norm pinned from a bubble. Ctrl+click on a ⓘ opens the norm in Woodcore's reader (norm_reader) or a map's site. A tab is `class SnowTab(DeclaredTabMixin, LoadTab)` and names its module; the snow is the first (snow_tab.py), the wind the next (D-1).

**Two paths, one base** (D-25): a tab that mixes this in takes the new frame, the others keep `LoadTab`'s -- the permanent loads and the wind until their own issues. The mixin overrides only the hooks `LoadTab` exposes (`build_inputs`, `fill_inputs`, `draft_inputs`, `build_result`, `refresh`, `fill_results`, `fill_figure`, `view_state`, `restore`) and asks nothing of `LoadTab` that `SourceEditorTab` does not give, so that the member checks may take it too (§13 of the spec).

**What the domain says, the base draws**: no word, no number and no rule of a domain is written here (tests/test_calc_tab_base.py mounts it on an invented domain and greps this file for the snow). The domain's words are its tab's (`<prefix>s_<section>`, `<prefix>f_<key>`, `<prefix>msg_<code>`, `<prefix>x_<excerpt>`), the base's `ct_` (calc_tab_words.py).
"""

import traceback

from PySide6.QtCore import QByteArray, QPointF, QRectF, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont, QPainter, QPen
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QGridLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget

import cards
import module_pane
import norm_bubble
import norm_reader
import project
import richtext
import theme
import validation
from domains.contracts import Message
from norms import excerpts as norm_excerpts


def _n(value):
    text = ("%.3f" % value).rstrip("0").rstrip(".")
    return "0" if text in ("", "-0") else text


def _words(params):
    """A message's values as its words print them: a number short, the rest as it is."""
    return {k: _n(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else v for k, v in params.items()}


# The right pane's narrowest: a module's header and a drawing stay readable beside a wide form
MODULES_MIN_WIDTH = 340


class _StateBody(QWidget):
    """The module «État du calcul» (REQ-008): in red what stops the calculation, in orange what is only said, in green that every input is there and the calculation made -- a click on a message takes the engineer to its field, which flashes."""

    def __init__(self, tab):
        super().__init__()
        self.tab = tab
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(0, 0, 0, 0)
        self.column.setSpacing(4)
        self.rows = []

    def refresh(self):
        for row in self.rows:
            row.setParent(None)
        self.rows = []
        messages = self.tab.messages_
        errors = [m for m in messages if m.severity == "error"]
        lines = [(m, "danger") for m in errors]
        if not errors and self.tab.instance is not None:
            lines.append((None, "ok"))
        lines += [(m, "warning") for m in messages if m.severity == "info"]
        for message, callout in lines:
            text = ("✓ " + self.tab.t("ct_complete")) if message is None else self.tab.message_text(message)
            label = QLabel(text)
            label.setWordWrap(True)
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setProperty("callout", callout if callout != "ok" else "info")
            if callout == "ok":
                label.setStyleSheet("color: %s;" % theme.colour("ok"))
            if message is not None and message.field:
                label.setCursor(Qt.CursorShape.PointingHandCursor)
                label.mousePressEvent = lambda _event, field=message.field: self.tab.focus_field(field)
            self.column.addWidget(label)
            self.rows.append(label)


class _ResultsBody(QWidget):
    """The module «Résultats» (REQ-009): what is computed, never an input, compact -- a row a value."""

    def __init__(self, tab):
        super().__init__()
        self.tab = tab
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel()
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        column.addWidget(self.label)

    def refresh(self):
        self.label.setText(self.tab.results_html())


class _DrawingBody(QWidget):
    """The domain's drawing of the case (the snow's column of Figur 3), as the export writes it, its words the window's."""

    def __init__(self, tab):
        super().__init__()
        self.tab = tab
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        self.svg = QSvgWidget()
        self.svg.setMinimumHeight(200)
        self.svg.setMinimumWidth(60)
        self.svg.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        column.addWidget(self.svg)

    def refresh(self):
        drawing = self.tab.drawing
        self.svg.setVisible(bool(drawing))
        if drawing:
            try:
                self.svg.load(QByteArray(drawing.encode("utf-8")))
                self.svg.renderer().setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
                size = self.svg.renderer().defaultSize()
                if size.width() > 0:
                    self.svg.setMinimumHeight(min(620, round(size.height() * min(max(self.width(), 260), size.width()) / size.width())))
            except Exception:  # broad: a drawing that fails must not empty the form -- but it is said (G5)
                traceback.print_exc()


class ChartWidget(QWidget):
    """An interactive chart of a domain's data (UI-010: Figur 2): its series as polylines, the case's marks, and under the pointer the value of every series there. It knows the labels the domain gives (`chart`: x, y, series, marks), never what they mean."""

    def __init__(self, tab):
        super().__init__()
        self.tab = tab
        self.setMouseTracking(True)
        self.setMinimumSize(320, 220)
        self.pointer = None
        self.data = None

    def refresh(self):
        self.data = self.tab.chart_data
        self.update()

    def _frame(self):
        return QRectF(40, 12, max(self.width() - 56, 10), max(self.height() - 44, 10))

    def _to(self, x, y):
        d, f = self.data, self._frame()
        sx = (x - d["x"]["min"]) / ((d["x"]["max"] - d["x"]["min"]) or 1)
        sy = (y - d["y"]["min"]) / ((d["y"]["max"] - d["y"]["min"]) or 1)
        return QPointF(f.left() + sx * f.width(), f.bottom() - sy * f.height())

    @staticmethod
    def value_at(points, x):
        """The series' value at `x`: straight between its points, constant beyond them."""
        if x <= points[0][0]:
            return points[0][1]
        for (x0, y0), (x1, y1) in zip(points, points[1:]):
            if x <= x1:
                return y0 + (y1 - y0) * (x - x0) / ((x1 - x0) or 1)
        return points[-1][1]

    def probe(self, x):
        """[(series name, value)] at `x` -- what the pointer reads."""
        return [(s["name"], self.value_at(s["points"], x)) for s in (self.data or {}).get("series", ())]

    def mouseMoveEvent(self, event):
        self.pointer = event.position()
        self.update()

    def leaveEvent(self, event):
        self.pointer = None
        self.update()

    def paintEvent(self, event):
        if not self.data:
            return
        d, f = self.data, self._frame()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        ink, muted, line = QColor(theme.colour("ink")), QColor(theme.colour("muted")), QColor(theme.colour("line"))
        p.setPen(QPen(line, 1, Qt.PenStyle.DashLine))
        x = d["x"]["min"]
        while x <= d["x"]["max"] + 1e-9:
            a = self._to(x, d["y"]["min"])
            p.drawLine(a, self._to(x, d["y"]["max"]))
            p.setPen(QPen(muted))
            p.drawText(QRectF(a.x() - 20, f.bottom() + 2, 40, 14), Qt.AlignmentFlag.AlignHCenter, _n(x))
            p.setPen(QPen(line, 1, Qt.PenStyle.DashLine))
            x += d["x"]["step"]
        y = d["y"]["min"]
        while y <= d["y"]["max"] + 1e-9:
            a = self._to(d["x"]["min"], y)
            p.drawLine(a, self._to(d["x"]["max"], y))
            p.setPen(QPen(muted))
            p.drawText(QRectF(0, a.y() - 7, 36, 14), Qt.AlignmentFlag.AlignRight, _n(y))
            p.setPen(QPen(line, 1, Qt.PenStyle.DashLine))
            y += d["y"]["step"]
        p.setPen(QPen(ink, 1))
        p.drawRect(f)
        p.drawText(QRectF(f.right() - 60, f.bottom() + 16, 60, 14), Qt.AlignmentFlag.AlignRight, "%s [%s]" % (d["x"]["label"], d["x"]["unit"]) if d["x"]["unit"] else d["x"]["label"])
        p.drawText(QRectF(2, 0, 36, 12), Qt.AlignmentFlag.AlignLeft, d["y"]["label"])
        for s in d["series"]:
            p.setPen(QPen(ink, 1.6))
            points = [self._to(px, py) for px, py in s["points"]]
            for a, b in zip(points, points[1:]):
                p.drawLine(a, b)
            last = points[-1]
            p.drawText(QRectF(last.x() - 36, last.y() - 16, 34, 14), Qt.AlignmentFlag.AlignRight, richtext.plain_math(s["name"]))
        accent = QColor(theme.colour("accent"))
        for m in d["marks"]:
            at = self._to(m["x"], m["y"])
            p.setPen(QPen(accent, 1, Qt.PenStyle.DashLine))
            p.drawLine(self._to(m["x"], d["y"]["min"]), at)
            p.setPen(QPen(accent, 1))
            p.setBrush(accent)
            p.drawEllipse(at, 4, 4)
            p.setBrush(Qt.BrushStyle.NoBrush)
            bold = QFont(p.font())
            bold.setBold(True)
            p.setFont(bold)
            p.drawText(QPointF(at.x() + 6, at.y() - 6), "%s = %s° → %s = %s" % (richtext.plain_math(m["label"]), _n(m["x"]), richtext.plain_math(m["series"]), "%.2f" % m["y"]))
            p.setFont(QFont(self.font()))
        if self.pointer is not None and f.contains(self.pointer):
            sx = (self.pointer.x() - f.left()) / f.width()
            x = d["x"]["min"] + sx * (d["x"]["max"] - d["x"]["min"])
            p.setPen(QPen(muted, 1))
            p.drawLine(QPointF(self.pointer.x(), f.top()), QPointF(self.pointer.x(), f.bottom()))
            said = "%s = %s°   " % (d["x"]["label"], _n(round(x))) + "   ".join("%s = %.2f" % (richtext.plain_math(name), value) for name, value in self.probe(x))
            p.setPen(QPen(ink))
            p.drawText(QRectF(f.left() + 4, f.top() + 2, f.width() - 8, 14), Qt.AlignmentFlag.AlignLeft, said)
        p.end()


class DeclaredTabMixin:
    """A tab of calculation built from its domain's declaration -- see the module's docstring. Mixed in before `LoadTab`."""

    def declaration(self):
        return self.MODULE.declaration()

    # --- the form ----------------------------------------------------------------------

    def build_inputs(self):
        import calc_fields
        decl = self.declaration()
        self.bubbles = norm_bubble.BubbleController(self.t, lambda: self.app.lang, self)
        self.bubbles.pinned.connect(self.pin_excerpts)
        self.bubbles.opened.connect(self.open_excerpt)
        self.fields, self.rows = {}, {}
        self.messages_, self.drawing, self.chart_data = [], None, None
        for section, keys in decl.sections:
            box = cards.card(self.t(decl.prefix + "s_" + section))
            form = cards.form(box)
            for key in keys:
                field = calc_fields.FieldWidget(self, decl.field(key), decl)
                form.addRow(field.label, field.widget)
                self.fields[key] = field
                self.rows[key] = (form, field.widget)
            self.form.addWidget(box)

    def custom_field(self, field):
        """A field of kind `custom`: (its widget, fill(src), draft(src)) -- the tab's own (the layers of a permanent load)."""
        raise NotImplementedError("%s declares a custom field %r and builds none" % (type(self).__name__, field.key))

    def fill_inputs(self, s):
        for field in self.fields.values():
            field.fill(s)
        self.update_rows(s)

    def draft_inputs(self, s):
        for field in self.fields.values():
            field.draft(s)

    def field_changed(self, key):
        """A choice made -- a button, a tile -- the rows the source shows again (a roof's slopes), then the draft computed."""
        self.update_rows(self.draft())
        self.touch()

    def update_rows(self, src):
        visible = set(self.MODULE.visible_fields(src))
        for key, (form, widget) in self.rows.items():
            form.setRowVisible(widget, key in visible)

    def focus_field(self, key):
        """A message clicked (T49): its field shown, given the focus, flashed."""
        field = self.fields.get(key)
        if field is None:
            return
        field.focus()
        field.blink()

    # --- the right pane ----------------------------------------------------------------

    def build_result(self):
        self.message = QLabel("")     # what LoadTab says a draft it cannot preview with; the state module says the rest
        self.message.setVisible(False)
        self.pane = module_pane.ModulePane(self.t, self.KEY)
        self.pane.setMinimumWidth(MODULES_MIN_WIDTH)
        self.pane.add(module_pane.ModuleSpec("state", self.t("ct_module_state"), lambda: _StateBody(self), kind="state"))
        self.pane.add(module_pane.ModuleSpec("results", self.t("ct_module_results"), lambda: _ResultsBody(self), kind="results"))
        if hasattr(self.MODULE, "figure_svg"):
            self.pane.add(module_pane.ModuleSpec("drawing", self.t(self.declaration().prefix + "module_drawing"), lambda: _DrawingBody(self), kind="drawing"))
        if hasattr(self.MODULE, "chart"):
            self.pane.add(module_pane.ModuleSpec("chart", self.t(self.declaration().prefix + "module_chart"), lambda: ChartWidget(self), kind="chart"))
        holder = QWidget()
        column = QVBoxLayout(holder)
        column.setContentsMargins(0, 0, 0, 0)
        column.addWidget(self.message)
        column.addWidget(self.pane, 1)
        return holder

    def refresh(self, preview=True):
        """The draft computed at once (D-10 of v0.117): what the domain says of it, its results, its drawing, its chart and its call -- never a calculation of the tab's."""
        source = self.draft()
        self.instance, self.reason, self.drawing, self.chart_data = None, "", None, None
        self.messages_ = list(self.MODULE.messages(source))
        if not any(m.severity == "error" for m in self.messages_):
            try:
                self.MODULE.check_source(source, "%s/%s.json" % (self.MODULE.FOLDER, source.get("id") or "?"))
                self.instance = self.MODULE.build_instance(source, project.current())
                if hasattr(self.MODULE, "figure_svg"):
                    self.drawing = self.MODULE.figure_svg(source, self.app.lang)
            except (validation.ValidationError, ValueError, KeyError, TypeError, ZeroDivisionError) as exc:
                self.reason = str(exc)
                self.messages_.insert(0, Message("invalid", None, "error", {"error": str(exc)}))
        if hasattr(self.MODULE, "chart"):
            try:
                self.chart_data = self.MODULE.chart(source)
            except (KeyError, TypeError, ValueError):
                self.chart_data = None
        self.message.setVisible(False)
        self.pane.refresh()
        self.update_summaries()
        self.fill_command()
        self.update_list_marker()
        if preview:
            self.request_preview()

    def fill_results(self):
        self.pane.refresh("results")

    def fill_figure(self):
        self.pane.refresh("drawing")

    def message_text(self, message):
        """A message in the window's words: the domain's `<prefix>msg_<code>`, the base's for a source it could not compute."""
        if message.code == "invalid":
            return self.t("ld_invalid", error=message.params.get("error", ""))
        return self.t(self.declaration().prefix + "msg_" + message.code, **_words(message.params))

    def results_html(self):
        if self.instance is None:
            return "<span style='color:%s'>%s</span>" % (theme.colour("muted"), richtext.escape(self.t("ct_none")))
        loads = set(self.instance.get("results") or ())
        rows = []
        for name in self.MODULE.results(self.instance):
            var = self.instance["vars"][name]
            value = var.get("value")
            text = _n(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else self.tl(str(value))
            unit = (" " + richtext.escape(var["unit"])) if var.get("unit") else ""
            weight = "font-weight:600;" if name in loads else ""
            rows.append("<tr style='%s'><td style='padding-right:6px'>%s</td><td style='padding-right:4px'>=</td><td align='right'>%s%s</td></tr>"
                        % (weight, richtext.math_html(var.get("symbol") or name), richtext.escape(text), unit))
        return '<table cellspacing="0" cellpadding="1">' + "".join(rows) + "</table>"

    def update_summaries(self):
        """What a folded module says in its header (T45): the state's count, the first load, the chart's marks."""
        errors = [m for m in self.messages_ if m.severity == "error"]
        infos = [m for m in self.messages_ if m.severity == "info"]
        if errors:
            state = self.t("ct_summary_errors", count=len(errors))
        else:
            state = self.t("ct_summary_complete") + ((" · " + self.t("ct_summary_infos", count=len(infos))) if infos else "")
        self.pane.summary("state", richtext.escape(state))
        first = next(iter((self.instance or {}).get("results") or ()), None)
        if first:
            var = self.instance["vars"][first]
            self.pane.summary("results", "%s = %s %s" % (richtext.math_html(var.get("symbol") or first), _n(var["value"]), richtext.escape(var.get("unit") or "")))
        else:
            self.pane.summary("results", richtext.escape(self.t("ct_none")))
        marks = (self.chart_data or {}).get("marks") or ()
        self.pane.summary("chart", " · ".join("%s → %s = %.2f" % (richtext.math_html(m["label"]), richtext.math_html(m["series"]), m["y"]) for m in marks))

    # --- «Affichage»: the case's file, line by line (domain_file_display) ------------------

    def install_display(self, cache_key, centre=1, right=2):
        """«Affichage» is the case's file set line by line (REQ-011 to REQ-015), in place of LoadTab's: the same panes, the same page."""
        import display_view
        import domain_file_display
        self.display = domain_file_display.DomainFileDisplay(self, cache_key)
        self.panes = display_view.ViewPanes(self.splitter, self.display, centre, right)
        self.view = self.VIEWS[0]

    def export_sources(self):
        """The export rebuilt with the case saved (LoadTab), then the cases' files of its kind written or refreshed -- what «Affichage» shows and a section includes, there as soon as the case is saved (REQ-015), as a member check's is (unfold.unfold_checks)."""
        import json
        from domains import unfold
        super().export_sources()
        here = project.current()
        data = json.loads((here.data_dir / "calculations.json").read_text(encoding="utf-8"))
        with project.using(here):
            unfold.unfold_domains(here, self.MODULE.DOMAIN, data)

    def _write_file(self, write):
        """One write of «Affichage» into the case's file (calc/domains/unfold_display.py), then the card and the page again -- refused with its reason in the status line."""
        from domains import unfold
        here = project.current()
        try:
            with project.using(here):
                write(here)
        except (unfold.UnfoldError, validation.ValidationError, OSError) as exc:
            if hasattr(self.app, "set_status"):
                self.app.set_status(self.t("ct_refused", error=str(exc)))
            return False
        self.display.rebuild()
        self.display.refresh()
        return True

    def write_line_display(self, line_id, values):
        """An argument of a line's display -- its level among them -- set in «Affichage» (REQ-012, REQ-013): written into the file, kept by the exports (D-17)."""
        from domains import unfold_display
        return self._write_file(lambda here: unfold_display.set_display(here, self.current_id, line_id, values, self.MODULE.DOMAIN))

    def write_figure(self, line_id, **parts):
        """The figure's width, caption, label, or whether it is shown (REQ-016, D-23, D-29)."""
        from domains import unfold_display
        return self._write_file(lambda here: unfold_display.set_figure(here, self.current_id, line_id, **parts))

    def write_unfold_regenerate(self):
        """«Régénérer» (D-18): a case's file of an earlier form written again in today's, the engineer's lines kept; lines changed on both sides are left to the «Formules» tab, which asks line by line."""
        from domains import unfold

        def regenerate(here):
            found = unfold.regenerate(here, self.current_id, kind=self.MODULE.DOMAIN)
            if found.get("conflicts"):
                raise unfold.UnfoldError(self.t("ct_conflicts", lines=", ".join(found["conflicts"])), "conflicts")
        return self._write_file(regenerate)

    def write_domain_level(self, level):
        """The domain's level, auto, 1, 2 or 3 (REQ-011, D-30)."""
        from domains import unfold_display
        return self._write_file(lambda here: unfold_display.set_domain_level(here, self.current_id, level, self.MODULE.DOMAIN))

    # --- the norm: pinned, opened ---------------------------------------------------------

    def pin_excerpts(self, norm, ids):
        """A bubble clicked (REQ-003): its excerpts a module under «Résultats», once."""
        items = [norm_excerpts.excerpt(norm, eid, self.app.lang) for eid in ids]
        prefix = self.declaration().prefix
        title = " + ".join("%s %s" % (e.ref, self.t(prefix + "x_" + e.id)) for e in items)
        spec = module_pane.ModuleSpec("x:" + norm + ":" + "+".join(ids), title, lambda: norm_bubble.ExcerptView(items, self.t), closable=True, kind="excerpt")
        return self.pane.pin(spec)

    def open_excerpt(self, norm, eid):
        """Ctrl+click (REQ-001, REQ-002): the excerpt's map where it has one, else the chapter in Woodcore's reader, the clause framed."""
        e = norm_excerpts.excerpt(norm, eid, self.app.lang)
        if e.map_url:
            QDesktopServices.openUrl(QUrl(e.map_url))
            return e.map_url
        shown = norm_reader.reader(self.app).show_excerpt(e)
        if not shown and hasattr(self.app, "set_status"):
            self.app.set_status(self.t("ct_reader_missing", file=e.file))
        return shown

    # --- state across a rebuild (D-27) ------------------------------------------------------

    def view_state(self):
        state = super().view_state()
        state["pins"] = self.pane.state()
        return state

    def restore(self, state):
        super().restore(state)
        pins = (state or {}).get("pins") or {}
        for module_id in pins.get("pins", ()):
            _x, norm, ids = module_id.split(":", 2)
            module = self.pin_excerpts(norm, tuple(ids.split("+")))
            if module_id in pins.get("folded", ()):
                module.set_folded(True, save=False)

    def hideEvent(self, event):
        if hasattr(self, "bubbles"):
            self.bubbles.hide()
        super().hideEvent(event)
