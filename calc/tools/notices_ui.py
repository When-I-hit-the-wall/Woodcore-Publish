# -*- coding: utf-8 -*-
"""Woodcore's notices in the window: two indicators at the top right, and the panel they open (spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, UI-001 to UI-005; docs/ui/window.md §10quater).

The engineer, 07.10.2026: «En haut à droite de Woodcore, immédiatement à gauche des boutons de langue : [ 🔴 ] [ 🟠 ] … Créer deux indicateurs permanents mais discrets» · «Le symbole doit être coloré uniquement lorsqu'au moins une erreur critique existe» · «le symbole correspondant doit clignoter pendant environ 3 secondes» · «Ouvrir un grand panneau déroulant directement sous les indicateurs … ne doit pas dépasser en dehors de la fenêtre ; doit avoir une hauteur maximale ; doit devenir scrollable».

What is here, and what is not:

* **The bar** (`NoticeBar`): the activity chip (`ActivityChip`, what runs in the background, REQ-007), then the red octagon of the critical notices and the orange triangle of the warnings (`Indicator`), each with its count -- grey and quiet at zero, in its colour while one is there, blinking BLINK_MS after a new one. The bar is made again with the window's content (a language switch, a reload); what it shows is the process's store (calc/notifications.py), which outlives it.
* **The panel** (`NoticePanel`): a popup under the indicators, never past the window's edges, at most MAX_HEIGHT of the window high, scrolling beyond. The indicator clicked chooses which notices it shows first; the filter at its head shows the others. Each row opens on a click -- the whole sentence, the technical text as it was, the file, its line and column -- and offers **Copier** (calc/notifications.py copy_text: a block to hand to a developer or an AI), **Ouvrir le fichier** (VS Code at the line where there is one -- `opener`, given by the window, never `code.cmd`, which flashes a console -- else the file's own program) and **Supprimer**. **Tout supprimer** at its foot takes out what the filter shows. Deleting takes the notice out of the window and nothing else.
* **The words**: STRINGS below, merged into the window's (woodcore_gui), in three languages; a notice's own title and sentence are looked up through calc/notifications.py, so they change with the language even for notices already shown. The technical text is never translated.
* **No Qt in the store**: a notice reported from a thread reaches the bar through `NoticeBridge`, whose signal Qt queues onto the window's thread; a burst of notices -- an exception raised on every paint -- refreshes the bar once per REFRESH_MS, not once per notice.
"""

import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QFont, QFontMetrics, QGuiApplication, QKeySequence, QPainter, QPen, QPolygonF, QTextLayout
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMenu, QPlainTextEdit, QPushButton, QScrollArea, QToolButton, QVBoxLayout, QWidget,
)

import notifications
import theme

BLINK_MS = 3000       # how long an indicator blinks after a new notice (the engineer: «environ 3 secondes»)
BLINK_STEP_MS = 300   # one half-period of the blink
REFRESH_MS = 120      # a burst of notices refreshes the bar once
MAX_HEIGHT = 0.7      # the panel's height at most, as a fraction of the window's
PANEL_WIDTH = 560
ICON = 16

STRINGS = {
    "fr": {
        "notice_critical_tip": "{n} erreur(s) critique(s) — cliquer pour les voir",
        "notice_warning_tip": "{n} avertissement(s) — cliquer pour les voir",
        "notice_none_tip": "Aucune notification",
        "notice_panel_title": "Notifications",
        "notice_filter_critical": "Erreurs",
        "notice_filter_warning": "Avertissements",
        "notice_filter_all": "Toutes",
        "notice_empty": "Rien à signaler.",
        "notice_copy": "Copier",
        "notice_copied": "Copié ✓",
        "notice_copy_all": "Tout copier",
        "notice_open": "Ouvrir le fichier",
        "notice_open_missing": "Le fichier n'existe plus : {file}",
        "notice_delete": "Supprimer",
        "notice_delete_all": "Tout supprimer",
        "notice_file": "Fichier",
        "notice_line": "Ligne {line}",
        "notice_column": "colonne {column}",
        "notice_source": "Source",
        "notice_technical": "Détails techniques",
        "notice_severity_critical": "Erreur critique",
        "notice_severity_warning": "Avertissement",
        "notice_severity_info": "Information",
        "notice_severity_success": "Succès",
        "notice_schema_unreadable_title": "Schéma ignoré",
        "notice_schema_unreadable": "Le schéma {file} est laissé de côté : il ne se lit pas — {error}",
        "notice_materials_moved_title": "Matériaux versés dans votre bibliothèque",
        "notice_materials_moved": "{n} matériau(x) saisi(s) dans ce projet sont maintenant dans votre bibliothèque (onglet Matériaux), le projet en garde une copie : {names}",
        "notice_command_removed_title": "Commande retirée",
        "notice_command_removed": "{file}, ligne {line} : {name} n'existe plus — {hint}",
        "notice_unit_scope_title": "Portée de #unit",
        "notice_unit_scope": "{file}, ligne {line} : #unit sans scope: ne vaut plus que pour la réponse suivante de sa dimension — écrire scope: \"document\" pour l'ancienne portée",
        "notice_exception_title": "Erreur inattendue",
        "notice_exception": "Une erreur inattendue s'est produite : {error}. L'opération en cours n'a peut-être pas abouti.",
        "notice_typst_error_title": "Compilation Typst impossible",
        "notice_typst_error": "Impossible de compiler le document : {message}",
        "notice_typst_warning_title": "Avertissement de Typst",
        "notice_typst_warning": "Typst signale : {message}",
        "notice_process_output_title": "Message d'un processus",
        "notice_process_output": "Un processus lancé par Woodcore a écrit : {first}",
        "notice_note_title": "Avertissement de l'export",
        "activity_one": "Chargement…",
        "activity_layers": "Export des calques",
        "activity_preview": "Aperçu Typst",
        "activity_sheet": "Rendu de la feuille",
        "activity_many": "{n} tâches…",
    },
    "de": {
        "notice_critical_tip": "{n} kritische(r) Fehler — klicken, um sie zu sehen",
        "notice_warning_tip": "{n} Warnung(en) — klicken, um sie zu sehen",
        "notice_none_tip": "Keine Meldungen",
        "notice_panel_title": "Meldungen",
        "notice_filter_critical": "Fehler",
        "notice_filter_warning": "Warnungen",
        "notice_filter_all": "Alle",
        "notice_empty": "Nichts zu melden.",
        "notice_copy": "Kopieren",
        "notice_copied": "Kopiert ✓",
        "notice_copy_all": "Alle kopieren",
        "notice_open": "Datei öffnen",
        "notice_open_missing": "Die Datei gibt es nicht mehr: {file}",
        "notice_delete": "Löschen",
        "notice_delete_all": "Alle löschen",
        "notice_file": "Datei",
        "notice_line": "Zeile {line}",
        "notice_column": "Spalte {column}",
        "notice_source": "Quelle",
        "notice_technical": "Technische Angaben",
        "notice_severity_critical": "Kritischer Fehler",
        "notice_severity_warning": "Warnung",
        "notice_severity_info": "Information",
        "notice_severity_success": "Erfolg",
        "notice_schema_unreadable_title": "Schema übergangen",
        "notice_schema_unreadable": "Das Schema {file} wird übergangen: Es lässt sich nicht lesen — {error}",
        "notice_materials_moved_title": "Materialien in Ihre Bibliothek übernommen",
        "notice_materials_moved": "{n} in diesem Projekt erfasste(s) Material(ien) sind jetzt in Ihrer Bibliothek (Register Materialien), das Projekt behält eine Kopie: {names}",
        "notice_command_removed_title": "Befehl entfernt",
        "notice_command_removed": "{file}, Zeile {line}: {name} gibt es nicht mehr — {hint}",
        "notice_unit_scope_title": "Reichweite von #unit",
        "notice_unit_scope": "{file}, Zeile {line}: #unit ohne scope: gilt nur noch für das nächste Ergebnis seiner Dimension — scope: \"document\" schreiben für die frühere Reichweite",
        "notice_exception_title": "Unerwarteter Fehler",
        "notice_exception": "Ein unerwarteter Fehler ist aufgetreten: {error}. Der laufende Vorgang ist möglicherweise nicht abgeschlossen.",
        "notice_typst_error_title": "Typst-Kompilierung unmöglich",
        "notice_typst_error": "Das Dokument lässt sich nicht kompilieren: {message}",
        "notice_typst_warning_title": "Warnung von Typst",
        "notice_typst_warning": "Typst meldet: {message}",
        "notice_process_output_title": "Meldung eines Prozesses",
        "notice_process_output": "Ein von Woodcore gestarteter Prozess hat geschrieben: {first}",
        "notice_note_title": "Warnung des Exports",
        "activity_one": "Laden…",
        "activity_layers": "Export der Ebenen",
        "activity_preview": "Typst-Vorschau",
        "activity_sheet": "Blatt wird gerendert",
        "activity_many": "{n} Aufgaben…",
    },
    "en": {
        "notice_critical_tip": "{n} critical error(s) — click to see them",
        "notice_warning_tip": "{n} warning(s) — click to see them",
        "notice_none_tip": "No notices",
        "notice_panel_title": "Notices",
        "notice_filter_critical": "Errors",
        "notice_filter_warning": "Warnings",
        "notice_filter_all": "All",
        "notice_empty": "Nothing to report.",
        "notice_copy": "Copy",
        "notice_copied": "Copied ✓",
        "notice_copy_all": "Copy all",
        "notice_open": "Open the file",
        "notice_open_missing": "The file no longer exists: {file}",
        "notice_delete": "Delete",
        "notice_delete_all": "Delete all",
        "notice_file": "File",
        "notice_line": "Line {line}",
        "notice_column": "column {column}",
        "notice_source": "Source",
        "notice_technical": "Technical details",
        "notice_severity_critical": "Critical error",
        "notice_severity_warning": "Warning",
        "notice_severity_info": "Information",
        "notice_severity_success": "Success",
        "notice_schema_unreadable_title": "Schema left out",
        "notice_schema_unreadable": "The schema {file} is left out: it does not read — {error}",
        "notice_materials_moved_title": "Materials moved into your library",
        "notice_materials_moved": "{n} material(s) typed in this project are now in your library (Materials tab), the project keeps a copy: {names}",
        "notice_command_removed_title": "Command removed",
        "notice_command_removed": "{file}, line {line}: {name} no longer exists — {hint}",
        "notice_unit_scope_title": "Reach of #unit",
        "notice_unit_scope": "{file}, line {line}: #unit without scope: now reaches only the next answer of its dimension — write scope: \"document\" for its former reach",
        "notice_exception_title": "Unexpected error",
        "notice_exception": "An unexpected error occurred: {error}. The operation under way may not have been completed.",
        "notice_typst_error_title": "Typst compilation failed",
        "notice_typst_error": "The document cannot be compiled: {message}",
        "notice_typst_warning_title": "Typst warning",
        "notice_typst_warning": "Typst reports: {message}",
        "notice_process_output_title": "Output of a process",
        "notice_process_output": "A process Woodcore started wrote: {first}",
        "notice_note_title": "Warning of the export",
        "activity_one": "Loading…",
        "activity_layers": "Exporting the layers",
        "activity_preview": "Typst preview",
        "activity_sheet": "Rendering the sheet",
        "activity_many": "{n} tasks…",
    },
}

def words(lang):
    """This module's own words in `lang`, as a `t(key, **values)` -- for a window that has no glossary of its own holding them, the start page."""
    table = STRINGS[lang if lang in STRINGS else "en"]
    return lambda key, **values: table[key].format(**values) if values else table[key]


# The colour of each severity shown, a token of theme.json.
COLOURS = {notifications.CRITICAL: "danger", notifications.WARNING: "warning"}


def elide_path(path, metrics, width):
    """A long path cut in its middle, its drive and its file name kept: what a row shows; the whole path is its tooltip and is copied."""
    return metrics.elidedText(str(path), Qt.TextElideMode.ElideMiddle, int(width))


def paint_symbol(painter, rect, severity, colour, filled=True):
    """The red octagon of a stop sign for a critical notice, the triangle of a warning sign for a warning: `colour` filled with a white mark where `filled`, an outline in `colour` otherwise (an indicator at zero)."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    r = QRectF(rect).adjusted(1, 1, -1, -1)
    if severity == notifications.CRITICAL:
        cut = r.width() * 0.2929   # (1 - 1/√2) of the side: a regular octagon in the square
        points = [QPointF(r.left() + cut, r.top()), QPointF(r.right() - cut, r.top()), QPointF(r.right(), r.top() + cut), QPointF(r.right(), r.bottom() - cut),
                  QPointF(r.right() - cut, r.bottom()), QPointF(r.left() + cut, r.bottom()), QPointF(r.left(), r.bottom() - cut), QPointF(r.left(), r.top() + cut)]
    else:
        points = [QPointF(r.center().x(), r.top()), QPointF(r.right(), r.bottom()), QPointF(r.left(), r.bottom())]
    shape = QPolygonF(points)
    if filled:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(colour))
        painter.drawPolygon(shape)
        pen = QPen(theme.qcolor("badge-ink"), max(1.4, r.width() / 9))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        if severity == notifications.CRITICAL:   # a white bar across, as on the sign
            y = r.center().y()
            painter.drawLine(QPointF(r.left() + r.width() * 0.28, y), QPointF(r.right() - r.width() * 0.28, y))
        else:                               # the exclamation mark
            x = r.center().x()
            painter.drawLine(QPointF(x, r.top() + r.height() * 0.38), QPointF(x, r.top() + r.height() * 0.66))
            painter.drawPoint(QPointF(x, r.top() + r.height() * 0.82))
    else:
        painter.setPen(QPen(QColor(colour), 1.2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolygon(shape)
    painter.restore()


class NoticeBridge(QObject):
    """The store's changes carried onto the window's thread, a burst of them refreshing once."""

    changed = Signal()
    _poke = Signal()

    def __init__(self, store=None, parent=None):
        super().__init__(parent)
        self.store = store or notifications.STORE
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(REFRESH_MS)
        self._timer.timeout.connect(self.changed)
        self._poke.connect(self._schedule, Qt.ConnectionType.QueuedConnection)
        self._listener = self.store.listen(self._poke.emit)
        self.destroyed.connect(lambda *_a, store=self.store, listener=self._listener: store.unlisten(listener))

    def _schedule(self):
        if not self._timer.isActive():
            self._timer.start()


class Indicator(QToolButton):
    """One severity's symbol and count: quiet at zero, coloured from the first notice, blinking BLINK_MS after a new one."""

    def __init__(self, severity, parent=None):
        super().__init__(parent)
        self.severity = severity
        self.count = 0
        self.blink_until = 0.0
        self.setAutoRaise(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName(f"notice_{severity}")
        self._timer = QTimer(self)
        self._timer.setInterval(BLINK_STEP_MS)
        self._timer.timeout.connect(self._tick)
        self.setFixedHeight(26)

    def sizeHint(self):
        metrics = QFontMetrics(self.font())
        return QSize(ICON + 10 + metrics.horizontalAdvance(str(max(self.count, 0))) + 6, 26)

    def set_count(self, count, new=False):
        self.count = count
        if new and count:
            self.blink_until = time.monotonic() + BLINK_MS / 1000
            self._timer.start()
        if not count:
            self.blink_until = 0.0
            self._timer.stop()
        self.updateGeometry()
        self.update()

    def blinking(self):
        return self.count > 0 and time.monotonic() < self.blink_until

    def _tick(self):
        if not self.blinking():
            self._timer.stop()
        self.update()

    def lit(self):
        """Whether the symbol shows its colour now: always while there is a notice, but for the dark half of each blink."""
        if not self.count:
            return False
        if self.blinking():
            phase = int((self.blink_until - time.monotonic()) * 1000 / BLINK_STEP_MS)
            return phase % 2 == 0
        return True

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        colour = theme.colour(COLOURS[self.severity]) if self.count else theme.colour("muted")
        box = QRect(5, (self.height() - ICON) // 2, ICON, ICON)
        paint_symbol(painter, box, self.severity, colour if self.lit() or not self.count else theme.colour("line-strong"), filled=bool(self.count))
        painter.setPen(QColor(theme.colour("ink") if self.count else theme.colour("muted")))
        font = QFont(self.font())
        if self.count:
            font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(QRect(box.right() + 5, 0, self.width() - box.right() - 5, self.height()), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, str(self.count))
        painter.end()


class ActivityChip(QWidget):
    """What runs in the background (REQ-007): a small turning arc and «Chargement…», or «2 tâches…», their names in its tooltip. Its room is kept when nothing runs, so the bar never moves."""

    def __init__(self, t, parent=None):
        super().__init__(parent)
        self.t = t
        self.labels = []
        self.started = time.monotonic()
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self.update)
        policy = self.sizePolicy()
        policy.setRetainSizeWhenHidden(True)
        self.setSizePolicy(policy)
        self.setFixedHeight(26)
        self.setVisible(False)

    def sizeHint(self):
        metrics = QFontMetrics(self.font())
        text = max((self.t("activity_one"), self.t("activity_many", n=9)), key=metrics.horizontalAdvance)
        return QSize(ICON + 12 + metrics.horizontalAdvance(text), 26)

    def text(self):
        return self.t("activity_one") if len(self.labels) <= 1 else self.t("activity_many", n=len(self.labels))

    def word(self, label):
        """A task's name: the window's word where it is a key of it (`activity_…`), else as the caller gave it."""
        try:
            return self.t(label) if label.startswith("activity_") else label
        except KeyError:
            return label

    def set_tasks(self, labels):
        self.labels = list(labels)
        running = bool(self.labels)
        self.setToolTip("\n".join(self.word(label) for label in self.labels))
        if running and not self._timer.isActive():
            self.started = time.monotonic()
            self._timer.start()
        elif not running:
            self._timer.stop()
        self.setVisible(running)
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        box = QRectF(3, (self.height() - ICON) / 2 + 1, ICON - 2, ICON - 2)
        painter.setPen(QPen(QColor(theme.colour("line")), 2.2))
        painter.drawEllipse(box)
        pen = QPen(QColor(theme.colour("accent")), 2.2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        angle = (time.monotonic() - self.started) * 360 / 1.1
        painter.drawArc(box, int(-angle * 16), int(-100 * 16))
        painter.setPen(QColor(theme.colour("muted")))
        painter.drawText(QRect(ICON + 8, 0, self.width() - ICON - 8, self.height()), Qt.AlignmentFlag.AlignVCenter, self.text())
        painter.end()


SUMMARY_LINES = 3   # the lines of its message a closed row shows (issue #11), the whole when it is opened


class ElidedLabel(QLabel):
    """Plain words wrapped on at most `lines` lines at the label's own width, the last cut with an ellipsis where the text goes on -- worked out again at every width it is given (`resizeEvent`), never at the width it had when the text was set. The whole text in its tooltip while it is cut."""

    def __init__(self, text="", lines=SUMMARY_LINES, parent=None):
        super().__init__(parent)
        self.lines = lines
        self.whole = ""
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setWordWrap(True)
        self.set_whole(text)

    def set_whole(self, text):
        self.whole = text or ""
        self.fit()

    def shown_text(self, width):
        """What `whole` shows in `width` pixels: its first `lines` lines as wrapped there, the last ending in an ellipsis where more follows."""
        if width <= 0 or not self.whole:
            return self.whole
        metrics = QFontMetrics(self.font())
        shown, rest = [], self.whole
        layout = QTextLayout(rest, self.font())
        layout.beginLayout()
        lines = []
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(width)
            lines.append((line.textStart(), line.textLength()))
        layout.endLayout()
        if len(lines) <= self.lines:
            return self.whole
        for start, length in lines[:self.lines - 1]:
            shown.append(rest[start:start + length].rstrip())
        start = lines[self.lines - 1][0]
        shown.append(metrics.elidedText(rest[start:].replace("\n", " "), Qt.TextElideMode.ElideRight, width))
        return "\n".join(shown)

    def fit(self):
        text = self.shown_text(self.contentsRect().width())
        if text != self.text():
            super().setText(text)
        self.setToolTip("" if text == self.whole else self.whole)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit()


class NoticeRow(QFrame):
    """One notice in the panel: closed, its symbol, title, first line, time and count; open, everything about it and its actions."""

    def __init__(self, panel, notice):
        super().__init__()
        self.panel = panel
        self.notice = notice
        self.open = False
        self.setObjectName("noticeRow")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.box = QVBoxLayout(self)
        self.box.setContentsMargins(10, 6, 10, 6)
        self.box.setSpacing(3)
        t, lang = panel.t, panel.lang
        head = QHBoxLayout()
        head.setSpacing(8)
        symbol = QLabel()
        symbol.setFixedSize(ICON, ICON)
        symbol.paintEvent = lambda _e, s=symbol: self._paint_symbol(s)
        head.addWidget(symbol, 0, Qt.AlignmentFlag.AlignTop)
        title = QLabel(notifications.title(notice, lang))
        font = QFont(title.font())
        font.setWeight(QFont.Weight.DemiBold)
        title.setFont(font)
        title.setWordWrap(True)
        head.addWidget(title, 1)
        stamp = time.strftime("%H:%M:%S", time.localtime(notice.last or notice.timestamp))
        when = QLabel(stamp + (f"  ×{notice.count}" if notice.count > 1 else ""))
        when.setStyleSheet(f"color: {theme.colour('muted')};")
        head.addWidget(when, 0, Qt.AlignmentFlag.AlignTop)
        self.box.addLayout(head)
        self.summary = ElidedLabel(lines=SUMMARY_LINES)
        self.summary.setStyleSheet(f"color: {theme.colour('ink-soft')};")
        self.summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)   # issue #11: what is read can be copied, a part of it as the whole
        self.summary.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)   # the row's own menu (`contextMenuEvent`), and not the label's
        self.summary.installEventFilter(self)
        self.box.addWidget(self.summary)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)   # Ctrl+C on a row clicked (`keyPressEvent`)
        self.details = QWidget()
        self.details.setVisible(False)
        self.box.addWidget(self.details)
        self._fill_details()
        self._set_summary()

    def _paint_symbol(self, label):
        painter = QPainter(label)
        severity = self.notice.severity if self.notice.severity in COLOURS else notifications.WARNING
        paint_symbol(painter, label.rect(), severity, theme.colour(COLOURS[severity]))
        painter.end()

    def _set_summary(self):
        """The message, on up to SUMMARY_LINES lines at the row's own width and cut with an ellipsis after them (issue #11: «le message est coupé après les deux premiers mots» -- it was cut to one line at a width read before the panel had its own, `place`); whole once the row is opened."""
        text = notifications.message(self.notice, self.panel.lang).strip()
        self.summary.set_whole(text)

    def _fill_details(self):
        t = self.panel.t
        notice = self.notice
        box = QVBoxLayout(self.details)
        box.setContentsMargins(ICON + 8, 2, 0, 0)
        box.setSpacing(4)
        full = QLabel(notifications.message(notice, self.panel.lang))
        full.setWordWrap(True)
        full.setTextFormat(Qt.TextFormat.PlainText)
        full.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.addWidget(full)
        if notice.file:
            where = QLabel()
            where.setTextFormat(Qt.TextFormat.PlainText)
            metrics = QFontMetrics(where.font())
            place = [t("notice_line", line=notice.line)] if notice.line else []
            if notice.column:
                place.append(t("notice_column", column=notice.column))
            path = elide_path(notice.file, metrics, max(160, self.panel.width() - 140))
            where.setText(f"{t('notice_file')} : {path}" + (f"  —  {', '.join(place)}" if place else ""))
            where.setToolTip(notice.where())
            where.setObjectName("noticeFile")
            box.addWidget(where)
        if notice.source:
            source = QLabel(f"{t('notice_source')} : {notice.source}")
            source.setStyleSheet(f"color: {theme.colour('muted')};")
            box.addWidget(source)
        if notice.technical:
            label = QLabel(t("notice_technical"))
            label.setStyleSheet(f"color: {theme.colour('muted')};")
            box.addWidget(label)
            text = QPlainTextEdit(notice.technical.rstrip())
            text.setReadOnly(True)
            text.setObjectName("noticeTechnical")
            text.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
            mono = QFont(self.panel.mono_font or text.font())
            text.setFont(mono)
            lines = min(14, max(3, notice.technical.count("\n") + 2))
            text.setFixedHeight(QFontMetrics(mono).lineSpacing() * lines + 12)
            box.addWidget(text)
        actions = QHBoxLayout()
        actions.setSpacing(6)
        self.copy_button = QPushButton(t("notice_copy"))
        self.copy_button.clicked.connect(self.copy)
        actions.addWidget(self.copy_button)
        if notifications.OPEN_FILE in notice.actions and notice.file:
            self.open_button = QPushButton(t("notice_open"))
            exists = Path(notice.file).exists()
            self.open_button.setEnabled(exists)
            if not exists:
                self.open_button.setToolTip(t("notice_open_missing", file=notice.file))
            self.open_button.clicked.connect(lambda: self.panel.open_file(notice))
            actions.addWidget(self.open_button)
        else:
            self.open_button = None
        actions.addStretch(1)
        delete = QPushButton(t("notice_delete"))
        delete.clicked.connect(lambda: self.panel.delete(notice.id))
        actions.addWidget(delete)
        box.addLayout(actions)

    def toggle(self):
        self.open = not self.open
        self.details.setVisible(self.open)
        self.summary.setVisible(not self.open)

    def copy(self):
        self.panel.copy_notices([self.notice])
        self.copy_button.setText(self.panel.t("notice_copied"))
        QTimer.singleShot(1500, self.copy_button, lambda: self.copy_button.setText(self.panel.t("notice_copy")))   # tied to the button: a row deleted meanwhile takes the timer with it

    def eventFilter(self, watched, event):
        """A click on the summary opens the row, as a click anywhere on it does -- unless it selected a part of the text, which is a copy begun and not a row asked for (issue #11)."""
        if watched is self.summary and event.type() == event.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            if not self.summary.hasSelectedText():
                self.toggle()
            self.setFocus()
        return False

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self.details.geometry().contains(event.position().toPoint()):
            self.toggle()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        """Ctrl+C: the text selected in the summary where there is one, the whole notice otherwise (issue #11)."""
        if event.matches(QKeySequence.StandardKey.Copy):
            if self.summary.hasSelectedText():
                QGuiApplication.clipboard().setText(self.summary.selectedText())
            else:
                self.panel.copy_notices([self.notice])
            event.accept()
            return
        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """«Copier» and «Tout copier», a right click away, the row neither opened nor closed (issue #11)."""
        menu = QMenu(self)
        menu.addAction(self.panel.t("notice_copy"), lambda: self.panel.copy_notices([self.notice]))
        menu.addAction(self.panel.t("notice_copy_all"), self.panel.copy_all)
        menu.exec(event.globalPos())
        event.accept()


class NoticePanel(QFrame):
    """The drop-down under the indicators: a popup of its own, inside the window, scrolling past MAX_HEIGHT."""

    def __init__(self, bar):
        super().__init__(bar.window(), Qt.WindowType.Popup)
        self.bar = bar
        self.t, self.lang = bar.t, bar.lang
        self.mono_font = bar.mono_font
        self.filter = notifications.CRITICAL
        self.setObjectName("noticePanel")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            f"QFrame#noticePanel {{ background: {theme.colour('card')}; border: 1px solid {theme.colour('line-strong')}; border-radius: 8px; }}"
            f" QFrame#noticeRow {{ border-bottom: 1px solid {theme.colour('line')}; }}"
            f" QFrame#noticeRow:hover {{ background: {theme.colour('bg-soft')}; }}")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 8, 0, 8)
        outer.setSpacing(6)
        head = QHBoxLayout()
        head.setContentsMargins(12, 0, 12, 0)
        title = QLabel(self.t("notice_panel_title"))
        font = QFont(title.font())
        font.setWeight(QFont.Weight.DemiBold)
        title.setFont(font)
        head.addWidget(title)
        head.addStretch(1)
        self.filters = {}
        for key in (notifications.CRITICAL, notifications.WARNING, "all"):
            button = QToolButton()
            button.setCheckable(True)
            button.setAutoRaise(True)
            button.clicked.connect(lambda _c=False, key=key: self.set_filter(key))
            self.filters[key] = button
            head.addWidget(button)
        outer.addLayout(head)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.body = QWidget()
        self.rows = QVBoxLayout(self.body)
        self.rows.setContentsMargins(0, 0, 0, 0)
        self.rows.setSpacing(0)
        self.scroll.setWidget(self.body)
        outer.addWidget(self.scroll, 1)
        foot = QHBoxLayout()
        foot.setContentsMargins(12, 0, 12, 0)
        self.copy_all_button = QPushButton(self.t("notice_copy_all"))   # issue #11: every notice shown, as «Copier» gives one
        self.copy_all_button.clicked.connect(self.copy_all)
        foot.addWidget(self.copy_all_button)
        foot.addStretch(1)
        self.delete_all = QPushButton(self.t("notice_delete_all"))
        self.delete_all.clicked.connect(self.clear)
        foot.addWidget(self.delete_all)
        outer.addLayout(foot)
        bar.bridge.changed.connect(self.refresh)

    def context(self):
        return self.bar.context()

    def copy_notices(self, notices):
        """`notices` on the clipboard, each as «Copier» writes it (notifications.copy_all)."""
        QGuiApplication.clipboard().setText(notifications.copy_all(notices, self.lang, self.context()))

    def copy_all(self):
        self.copy_notices(self.notices_shown())

    def notices_shown(self):
        severity = None if self.filter == "all" else self.filter
        return self.bar.store.items(severity)

    def set_filter(self, key):
        self.filter = key
        self.refresh()

    def refresh(self):
        counts = self.bar.store.counts()
        for key, button in self.filters.items():
            n = sum(counts.values()) if key == "all" else counts.get(key, 0)
            button.setText(f"{self.t('notice_filter_' + key)} ({n})")
            button.setChecked(key == self.filter)
        open_ids = {self.rows.itemAt(i).widget().notice.id for i in range(self.rows.count())
                    if isinstance(self.rows.itemAt(i).widget(), NoticeRow) and self.rows.itemAt(i).widget().open}
        while self.rows.count():
            item = self.rows.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        shown = self.notices_shown()
        for notice in shown:
            row = NoticeRow(self, notice)
            if notice.id in open_ids:
                row.toggle()
            self.rows.addWidget(row)
        if not shown:
            empty = QLabel(self.t("notice_empty"))
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(f"color: {theme.colour('muted')}; padding: 18px;")
            self.rows.addWidget(empty)
        self.rows.addStretch(1)
        self.delete_all.setEnabled(bool(shown))
        self.copy_all_button.setEnabled(bool(shown))
        self.place()

    def place(self):
        """Under the indicators, inside the window: as wide as PANEL_WIDTH or the window allows, at most MAX_HEIGHT of it high."""
        window = self.bar.window()
        frame = QRect(window.mapToGlobal(QPoint(0, 0)), window.size())
        anchor = self.bar.mapToGlobal(QPoint(self.bar.width(), self.bar.height() + 4))
        width = min(PANEL_WIDTH, frame.width() - 16)
        x = max(frame.left() + 8, min(anchor.x() - width, frame.right() - width - 8))
        y = anchor.y()
        room = max(160, min(int(frame.height() * MAX_HEIGHT), frame.bottom() - y - 8))
        self.body.setFixedWidth(width - 2)
        wanted = self.body.sizeHint().height() + 90
        self.setGeometry(x, y, width, min(room, wanted))

    def delete(self, notice_id):
        self.bar.store.remove(notice_id)

    def clear(self):
        self.bar.store.clear(None if self.filter == "all" else self.filter)

    def open_file(self, notice):
        self.bar.open_file(notice)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)


class NoticeBar(QWidget):
    """The top bar's right corner, between the views and the languages (issue #11): the activity chip, the critical notices' octagon, the warnings' triangle (UI-001)."""

    def __init__(self, t, lang, store=None, opener=None, context=None, mono_font=None, status=None, parent=None):
        super().__init__(parent)
        self.t, self.lang = t, lang
        self.store = store or notifications.STORE
        self.opener = opener
        self.status = status   # where an information notice goes: the window's status line, one line, gone with the next
        self._context = context or (lambda: {})
        self.mono_font = mono_font
        self.panel = None
        self.bridge = NoticeBridge(self.store, self)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self.activity = ActivityChip(t)
        layout.addWidget(self.activity)
        self.indicators = {}
        for severity in (notifications.CRITICAL, notifications.WARNING):
            indicator = Indicator(severity)
            indicator.clicked.connect(lambda _c=False, severity=severity: self.show_panel(severity))
            self.indicators[severity] = indicator
            layout.addWidget(indicator)
        self._seen = {severity: {n.id for n in self.store.items(severity)} for severity in self.indicators}
        self.bridge.changed.connect(self.refresh)
        self.refresh(blink=False)
        # what runs in the background, from wherever it runs (tasks.activity)
        import tasks
        self._activity = tasks.activity()
        self._activity.changed.connect(self._on_activity)
        self._on_activity()

    def _on_activity(self):
        try:
            self.activity.set_tasks(self._activity.keys())
        except RuntimeError:   # the bar was made again (a language switch): the old one has nothing to show
            pass

    def context(self):
        try:
            return self._context()
        except Exception:  # broad: the context is a help to whoever reads the copy, never a reason to fail it
            return {}

    def refresh(self, blink=True):
        # an information is a line of the status bar, not a notice to keep: said there, then taken out of the store -- kept until a status bar has said it (one reported before the window was up waits for it)
        for notice in reversed(self.store.items(notifications.INFO)):
            if self.status is not None and self.status(notifications.message(notice, self.lang)) is not False:
                self.store.remove(notice.id)
        for severity, indicator in self.indicators.items():
            items = self.store.items(severity)
            ids = {n.id for n in items}
            counts_now = {n.id: n.count for n in items}
            # a notice not seen before blinks; the same critical error met again blinks again -- a warning repeated by every export run without a question does not
            again = severity == notifications.CRITICAL and any(counts_now[i] > c for i, c in getattr(self, "_counts", {}).get(severity, {}).items() if i in counts_now)
            new = bool(ids - self._seen[severity]) or again
            indicator.set_count(len(items), new=blink and new)
            tip = "notice_critical_tip" if severity == notifications.CRITICAL else "notice_warning_tip"
            indicator.setToolTip(self.t(tip, n=len(items)) if items else self.t("notice_none_tip"))
            self._seen[severity] = ids
            self._counts = getattr(self, "_counts", {})
            self._counts[severity] = counts_now

    def show_panel(self, severity):
        if self.panel is None:
            self.panel = NoticePanel(self)
        counts = self.store.counts()
        self.panel.filter = severity if counts.get(severity) else ("all" if sum(counts.values()) else severity)
        self.panel.refresh()
        self.panel.show()
        self.panel.raise_()

    def open_file(self, notice):
        """The notice's file opened at its line: VS Code where `opener` finds it, else the file's own program."""
        path = notice.file
        if not path or not Path(path).exists():
            return False
        if self.opener is not None:
            try:
                if self.opener(path, notice.line, notice.column):
                    return True
            except Exception as exc:  # broad: an editor that cannot be started is a notice, and the file still opens
                notifications.report_exception(exc, source="notices", severity=notifications.WARNING)
        return QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def set_tasks(self, labels):
        self.activity.set_tasks(labels)


# --- exceptions nobody caught --------------------------------------------------------------------

_installed = []


def install_hooks():
    """An exception no code caught -- in a slot, in a thread -- becomes a critical notice, its traceback its technical text, and is still printed where there is a console: PySide6 would print it and carry on, and under pythonw, where there is no console, a button whose handler raised simply did nothing (v0.77). Installed once, from the window's start."""
    if _installed:
        return
    _installed.append(True)

    def hook(kind, value, tb):
        if sys.stderr is not None:  # None under pythonw
            sys.__excepthook__(kind, value, tb)
        if issubclass(kind, KeyboardInterrupt):
            return
        notifications.report_exception(value, source="window", tb=tb)

    def thread_hook(args):
        if sys.stderr is not None:
            threading.__excepthook__(args)
        if args.exc_type is SystemExit:
            return
        notifications.report_exception(args.exc_value, source=f"thread {args.thread.name if args.thread else ''}".strip(), tb=args.exc_traceback)

    sys.excepthook = hook
    threading.excepthook = thread_hook


# --- what a module says, in place of a message box ------------------------------------------------

def tell_unreadable_schemas(problems):
    """A warning for each schema a tab left out because it does not read (schema.readable_sources: [(path, error)]), naming the file and what is wrong in it, and offering to open it -- the tab staying usable with the others (v0.117, issue #28: where `schemas()` once skipped it without a word). The same schema left out again counts once more rather than piling up (notifications.NoticeStore)."""
    for path, exc in problems:
        tell(f"The schema {Path(path).name} is left out: it does not read -- {exc}", notifications.WARNING, exc=exc, code="schema_unreadable",
             key="notice_schema_unreadable", args={"file": Path(path).name, "error": str(exc)}, source="schemas", file=str(path))


def tell_removed_commands(removals, here):
    """A warning for each call of a command or an argument taken away that a project's sections still write (commands_migrate.removals: [(path, line, name, hint)]), naming the file and the line and offering to open it: the project is carried over by hand, never rewritten (spec 2026-10-21-commandes-typst-refonte, REQ-020, CON-004); the export refuses the first."""
    for path, line, name, hint in removals:
        rel = here.rel(path)
        tell(f"{rel}, line {line}: {name} no longer exists -- {hint}", notifications.WARNING, code="command_removed",
             key="notice_command_removed", args={"file": rel, "line": line, "name": name, "hint": hint}, title_key="notice_command_removed_title",
             source="commands", file=str(path), line=line)


def tell_materials_moved(names):
    """The materials a project typed before issue #110, poured into the engineer's library at the opening (materials_migrate, REQ-015): named, once."""
    if names:
        text = f"{len(names)} material(s) typed in this project are now in your library (Materials tab), the project keeps a copy: {', '.join(names)}"
        tell(text, notifications.INFO, code="materials_moved", key="notice_materials_moved", args={"n": len(names), "names": ", ".join(names)},
             title_key="notice_materials_moved_title", source="materials")


def tell_unscoped_units(found, here):
    """A warning for each `#unit` without `scope:` a project's sections write (commands_migrate.unit_scope_notes: [(path, line)]): it reached the rest of the document until the spec 2026-10-21-commandes-typst-refonte and now reaches the next answer (CON-007) -- said, never rewritten."""
    for path, line in found:
        rel = here.rel(path)
        tell(f"{rel}, line {line}: #unit without scope: now reaches only the next answer of its dimension -- write scope: \"document\" for its former reach", notifications.WARNING, code="unit_scope",
             key="notice_unit_scope", args={"file": rel, "line": line}, title_key="notice_unit_scope_title", source="commands", file=str(path), line=line)


def tell(text, severity=notifications.CRITICAL, *, exc=None, code=None, key="", args=None, title_key="", source="", file="", line=None, column=None):
    """What a module of the window says where it once opened a message box (REQ-009): a notice, at `severity` -- critical where the operation asked for could not be done, a warning where it went on, `info` for what is only worth a line of the status bar. `text` is the sentence as the caller has it, in the window's language; `key` and `args` let it be written again in another language; `exc` gives the technical text, the code and the file it was about. Returns the notice kept."""
    values = getattr(exc, "values", None) or {}
    file = str(file or getattr(exc, "file", "") or values.get("file", "") or "")
    if file and not Path(file).is_absolute():
        try:
            import project
            file = str(project.current().root / file)
        except Exception:  # broad: a file that cannot be placed is named as it was, and not offered to be opened
            pass
    technical = "" if exc is None else f"{type(exc).__name__}: {exc}"
    return notifications.report(code or getattr(exc, "code", None) or "message", text, severity, key=key, args=args, title_key=title_key,
                          technical=technical, source=source, file=file, line=line, column=column)


def inline_error(dialog, text):
    """A refusal inside a modal dialog -- a form not filled in, a template that could not be archived --, said in the dialog itself, in a red band above its buttons, never in the panel: the panel lies behind the modal and cannot be reached while it is up (review A10 of spec 2026-10-07-performance-erreurs-plans-legendes). Empty `text` takes the band away. Returns the band."""
    band = dialog.findChild(QLabel, "dialogError")
    layout = dialog.layout()
    if band is None:
        band = QLabel()
        band.setObjectName("dialogError")
        band.setProperty("callout", "danger")
        band.setWordWrap(True)
        band.setTextFormat(Qt.TextFormat.PlainText)
        band.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if layout is not None:
            layout.insertWidget(max(0, layout.count() - 1), band)
    band.setText(str(text or ""))
    band.setVisible(bool(text))
    return band
