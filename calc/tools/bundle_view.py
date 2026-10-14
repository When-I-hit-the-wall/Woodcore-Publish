# -*- coding: utf-8 -*-
"""An export document -- a PDF bundle of the export sheets -- as the «Export» view shows it when its folder is chosen (v0.117; spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-016, D6, D9).

The engineer, 07.10.2026: «dans l'affichage "Export", on doit voir toutes les pages qui composent un document lorsqu'on navigue dans ses plans. On doit pouvoir modifier le nom, la description, l'étage, l'id du document. Par défaut, les valeurs sont reprises automatiquement lors de l'import dessus du premier plan.»

* **The pages** (`BundlePages`): every sheet of the bundle, one after the other in its order, as their previews show them -- each compiled into Woodcore's cache where its preview is missing or older than the sheet (sheet_editor.render, the editor's own compile), the previews put end to end (pypdf), all in a task (tasks.TaskRunner: the chip says it runs, the window stays free), and the result shown by QtPdf's own multi-page view. Nothing is written into the project: «Exporter le PDF groupé» writes Plans/<id>.pdf.
* **Its fields** (`BundleCard`): its id, its name, its description and its storey -- each the bundle's own, or, where it states none, the first plan's on its first sheet, shown in grey in the empty field (calc/sheets.py bundle_fields). Writing one is the caller's (`edited(field, value)`): an id names the PDF, a name renames the folder.
"""

import io
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt, Signal
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QStackedWidget, QVBoxLayout, QWidget

import cards

STRINGS = {
    "fr": {
        "bv_card": "Document d'export",
        "bv_id": "Id",
        "bv_name": "Nom",
        "bv_description": "Description",
        "bv_storey": "Étage",
        "bv_from_plan": "Vide : repris du premier plan posé ({value}).",
        "bv_note": "Les pages du document, dans l'ordre. L'id nomme le PDF groupé (Plans/<id>.pdf).",
        "bv_loading": "Préparation des pages…",
        "bv_empty": "Ce document ne contient encore aucune feuille : glissez-en dans son dossier.",
        "bv_failed": "Les pages n'ont pas pu être préparées : {error}",
        "activity_bundle": "Pages du document d'export",
    },
    "de": {
        "bv_card": "Exportdokument",
        "bv_id": "Id",
        "bv_name": "Name",
        "bv_description": "Beschreibung",
        "bv_storey": "Geschoss",
        "bv_from_plan": "Leer: vom ersten gesetzten Plan übernommen ({value}).",
        "bv_note": "Die Seiten des Dokuments, in ihrer Reihenfolge. Die Id benennt das gesammelte PDF (Plans/<id>.pdf).",
        "bv_loading": "Seiten werden vorbereitet…",
        "bv_empty": "Dieses Dokument enthält noch kein Blatt: Blätter in seinen Ordner ziehen.",
        "bv_failed": "Die Seiten konnten nicht vorbereitet werden: {error}",
        "activity_bundle": "Seiten des Exportdokuments",
    },
    "en": {
        "bv_card": "Export document",
        "bv_id": "Id",
        "bv_name": "Name",
        "bv_description": "Description",
        "bv_storey": "Storey",
        "bv_from_plan": "Empty: taken from the first plan put on it ({value}).",
        "bv_note": "The document's pages, in their order. The id names the bundled PDF (Plans/<id>.pdf).",
        "bv_loading": "Preparing the pages…",
        "bv_empty": "This document holds no sheet yet: drag sheets into its folder.",
        "bv_failed": "The pages could not be prepared: {error}",
        "activity_bundle": "Pages of the export document",
    },
}

FIELDS = ("id", "name", "description", "storey")


def pages_pdf(here, sheet_ids):
    """The previews of `sheet_ids`, end to end, as the bytes of one PDF -- each compiled into the cache where it is missing or older than its sheet. Qt-free: run in a task."""
    import sheets
    import sheet_editor
    from pypdf import PdfWriter
    writer = PdfWriter()
    for sid in sheet_ids:
        target = Path(sheet_editor.cache_target(here, sid))
        source = sheets.path(here, sid)
        if not target.is_file() or (source.is_file() and target.stat().st_mtime < source.stat().st_mtime):
            result = sheet_editor.render(here, sid, target)
            if not result.get("ok"):
                raise RuntimeError(f"{sid}: {result.get('message') or 'the sheet does not compile'}")
        writer.append(str(target))
    out = io.BytesIO()
    writer.write(out)
    writer.close()
    return out.getvalue()


class BundlePages(QStackedWidget):
    """Every page of an export document, read-only, one under the other (QtPdf's multi-page view), or a line saying why there are none."""

    def __init__(self, t, parent=None):
        super().__init__(parent)
        self.t = t
        self.note = QLabel()
        self.note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.note.setWordWrap(True)
        self.addWidget(self.note)
        self.view = QPdfView()
        self.view.setPageMode(QPdfView.PageMode.MultiPage)
        self.view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        self.addWidget(self.view)
        self.document = None
        self.buffer = None
        self.shown = None   # the key of what is shown: (bundle, sheets)

    def say(self, text):
        self.note.setText(text)
        self.setCurrentWidget(self.note)

    def show_pdf(self, data, key):
        buffer = QBuffer(self)
        buffer.setData(QByteArray(data))
        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        document = QPdfDocument(self)
        document.load(buffer)
        old_document, old_buffer = self.document, self.buffer
        self.document, self.buffer, self.shown = document, buffer, key
        self.view.setDocument(document)
        self.setCurrentWidget(self.view)
        if old_document is not None:
            old_document.close()
            old_document.deleteLater()
        if old_buffer is not None:
            old_buffer.close()
            old_buffer.deleteLater()

    def page_count(self):
        return self.document.pageCount() if self.document is not None else 0


class BundleCard(QWidget):
    """The right pane of an export document: its four fields, each its own or the first plan's in grey."""

    edited = Signal(str, str)   # (field, value) -- an empty value: the plan's again

    def __init__(self, t, parent=None):
        super().__init__(parent)
        self.t = t
        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        self.card = cards.card(t("bv_card"))
        form = cards.form(self.card)
        self.fields = {}
        for key in FIELDS:
            field = QLineEdit()
            field.editingFinished.connect(lambda key=key: self._finished(key))
            self.fields[key] = field
            form.addRow(t(f"bv_{key}"), field)
        form.addRow(cards.note(t("bv_note")))
        box.addWidget(self.card)
        box.addStretch(1)
        self.values = {}

    def load(self, fields):
        """`fields` as sheets.bundle_fields gives them: a field the bundle states is written in it, one it takes from its plan shown in grey."""
        self.values = dict(fields)
        for key, field in self.fields.items():
            derived = key != "name" and fields.get("derived", {}).get(key)
            field.blockSignals(True)
            field.setText("" if derived else str(fields.get(key) or ""))
            field.setPlaceholderText(str(fields.get(key) or "") if derived else "")
            field.setToolTip(self.t("bv_from_plan", value=fields.get(key) or "—") if derived else "")
            field.blockSignals(False)

    def _finished(self, key):
        text = self.fields[key].text().strip()
        derived = key != "name" and self.values.get("derived", {}).get(key)
        if text == ("" if derived else str(self.values.get(key) or "")):
            return   # nothing changed: nothing written (the focus leaving a field is no edit)
        if key == "name" and not text:
            self.fields[key].setText(str(self.values.get("name") or ""))
            return   # a bundle keeps a name: its folder needs one
        self.edited.emit(key, text)
