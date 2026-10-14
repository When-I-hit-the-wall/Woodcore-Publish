"""DrawingTab's documents -- imported, opened, renamed, deleted, their pages turned and cropped, the plans drawn on them, their frames, their layers exported -- a mixin of methods moved verbatim out of calc/tools/drawing_tab.py (issue #30). DrawingTab names it among its bases.
"""

import json
import threading
from pathlib import Path
from PySide6.QtCore import QByteArray, QModelIndex, QObject, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QScrollArea, QSlider, QSplitter, QStackedWidget, QToolButton, QVBoxLayout, QWidget,
)
import tasks  # what runs in the background, said by the chip at the top right (tasks.activity, v0.117)
import engine
import project  # where the project this tab works on is (calc/project.py)
import source_archive  # «Supprimer» archives (source_archive.py)
import validation
from domains import plan_documents  # the documents a plan is drawn on (v0.114)
from domains import plan_pages  # the plans of both kinds drawn on one page: turned together, exported together (v0.115)
import notifications  # every error, warning and information, gathered in one place (calc/notifications.py, v0.117)
import notices_ui  # what was a message box is a notice since v0.117 (notices_ui.tell)


class _Background:
    """The one export of a layer switched under way, shared by the two tabs of plans -- both export both kinds (plan_pages.export_drawings), so two at once would write data/ twice over. `again` is the export asked for while one runs: it runs next, in the same thread."""

    thread = None
    again = None
    lock = threading.Lock()


def _run_layer_export(here, notice):
    """The thread's work: the plans of both kinds exported, and once more for every export asked for meanwhile -- each said to the tab that asked for it; said by the chip at the top right for as long as it runs (tasks.activity, REQ-007)."""
    token = tasks.activity().begin("activity_layers")
    try:
        _export_layers(here, notice)
    finally:
        tasks.activity().end(token)


def _export_layers(here, notice):
    while True:
        error = None
        try:
            plan_pages.export_drawings(here)
        except Exception as exc:  # broad: a source that no longer validates, a background moved, a file held: said, and data/ left as the failing kind's export leaves it
            error = exc
        try:
            notice.done.emit(error)
        except RuntimeError:   # the tab is gone: nobody to tell
            pass
        with _Background.lock:
            following, _Background.again = _Background.again, None
            if following is None:
                return
        here, notice = following


class Blank(dict):
    """The values of a sentence, a hole the exception did not fill left empty: a refusal of plan_documents states the values its own sentence needs, not every one the window's sentence might."""

    def __missing__(self, key):
        return ""


def document_text(doc):
    """A document as the left pane lists it: «D01 – name / file», the name left out where it has none."""
    file = Path(doc.get("file", "")).name
    name = (doc.get("name") or "").strip()
    return f"{doc['id']} – {name} / {file}" if name else f"{doc['id']} – {file}"


class DrawingDocumentsMixin:
    """Methods of drawing_tab.DrawingTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def document_error_text(self, exc):
        """A refusal of plan_documents or cad.py in the window's language, by its code; any other with its English sentence inside the window's."""
        code = getattr(exc, "code", None)
        key = f"plan_doc_err_{code}"
        try:
            text = self.w(key)
        except KeyError:
            return self.w("plan_doc_err_other", error=exc)
        return text.format_map(Blank(getattr(exc, "values", {}) or {})).strip()

    def reload_documents(self, select=None):
        """The documents of this tab, read again and listed: «D01 – name / file» -- those it imported, and of those written before v0.116 the ones plan_pages.document_owner gives it (the engineer: the position plan and the fire protection plan never see each other's documents). One that cannot be read is listed in the position plans' tab, to be put right there."""
        here = project.current()
        self.documents = {}
        folder = plan_documents.source_dir(here)
        candidates = sorted(folder.glob("*.json"), key=lambda p: p.name.lower()) if folder.is_dir() else []
        usage = plan_pages.document_usage(here) if candidates else {}
        paths = []
        for path in candidates:
            try:
                doc = plan_documents.read(here, path.stem)
            except validation.ValidationError:
                doc = None
            owner = plan_pages.document_owner(doc, usage) if doc is not None else "plan"
            if owner == self.DOC_OWNER:
                paths.append((path, doc))
        self.filling = True
        self.doc_list.blockSignals(True)
        try:
            self.doc_list.clear()
            for path, doc in paths:
                self.documents[path.stem] = doc
                item = QListWidgetItem(document_text(doc) if doc else self.w("plan_doc_unreadable", id=path.stem))
                item.setData(Qt.ItemDataRole.UserRole, path.stem)
                self.doc_list.addItem(item)
                if path.stem == select:
                    self.doc_list.setCurrentItem(item)
        finally:
            self.doc_list.blockSignals(False)
            self.filling = False
        self.doc_hint.setVisible(not paths)
        self.delete_doc_button.setEnabled(bool(paths))

    def import_document(self):
        """«Importer…»: a file of the project imported as a document (plan_documents.import_file) -- listed, chosen and shown, every page of it, with no dialog of pages: ticking a page makes a plan of it. True where one was imported."""
        here = project.current()
        if getattr(self.app, "read_only", False):
            self.app.refuse_read_only()
            return False
        start = here.root / "01_Pläne"
        if not start.is_dir():
            start = here.root
        name, _filter = QFileDialog.getOpenFileName(self, self.w("plan_doc_choose"), str(start), self.w("plan_background_filter"))
        if not name:
            return False
        try:
            doc = plan_documents.import_file(here, name, owner=self.DOC_OWNER)
        except validation.ValidationError as exc:
            notices_ui.tell(self.document_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return False
        if not self.leave_plan():
            return False
        self.reload_documents(select=doc["id"])
        self.open_document(doc["id"])
        self.app.set_status(self.w("plan_doc_imported", file=Path(doc["file"]).name, id=doc["id"]))
        return True

    def open_document(self, docid):
        """The document `docid` in the middle, every page of it, and its card on the right."""
        self.doc_id = docid
        self.doc_page = None
        self.show_kind("document")
        self.doc_list.blockSignals(True)
        for row in range(self.doc_list.count()):
            if self.doc_list.item(row).data(Qt.ItemDataRole.UserRole) == docid:
                self.doc_list.setCurrentRow(row)
        self.doc_list.blockSignals(False)
        self.refresh_document_view()

    def refresh_document_view(self):
        """The document shown read again, handed to the view with the pages its plans are drawn on ticked and their crops drawn -- and the other kind's, muted, where the subclass names them (other_crops) --, and its card filled."""
        docid = self.doc_id
        doc = None
        if docid:
            self.documents.pop(docid, None)
            doc = self.document(docid)
        self.doc_view.set_document(project.current(), doc)
        pages, crops = self.document_crops(docid) if doc else ([], {})
        self.doc_view.set_used_pages(pages)
        other_pages, other = self.other_crops(docid) if doc else ([], {})
        for page, items in other.items():
            crops.setdefault(page, []).extend(dict(item, other=True) for item in items)
        self.doc_view.set_crops(crops)
        self.doc_view.set_other_pages(other_pages)
        self.doc_name_edit.blockSignals(True)
        self.doc_name_edit.setText((doc or {}).get("name", ""))
        self.doc_name_edit.blockSignals(False)
        self.doc_name_edit.setEnabled(doc is not None)
        self.doc_file_text.setText((doc or {}).get("file", ""))
        self.doc_pages_text.setText(str(len(doc["pages"])) if doc else "")
        for button in (self.doc_rotate_left, self.doc_rotate_right):
            button.setEnabled(doc is not None)

    def rename_document(self):
        doc = self.document(self.doc_id)
        if doc is None or getattr(self.app, "read_only", False):
            return
        name = self.doc_name_edit.text().strip()
        if name == (doc.get("name") or ""):
            return
        doc = dict(doc, name=name)
        try:
            plan_documents.write(project.current(), doc)
        except (validation.ValidationError, OSError) as exc:
            notices_ui.tell(self.document_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return
        self.documents[doc["id"]] = doc
        self.reload_documents(select=doc["id"])
        self.app.set_status(self.w("plan_doc_renamed", id=doc["id"]))

    def delete_document(self):
        """«Supprimer» under the documents: the document chosen goes into the archives of its folder, never deleted -- asking first where plans are drawn on it, which then stay, drawn on its file as it is."""
        docid = self.doc_id if self.view_kind == "document" else None
        item = self.doc_list.currentItem()
        docid = docid or (item.data(Qt.ItemDataRole.UserRole) if item is not None else None)
        if not docid:
            return False
        used = [pid for pid, _source in self.sources_on(docid)]
        if used and QMessageBox.question(self, "Woodcore", self.w("plan_doc_delete_used", plans=", ".join(used), id=docid)) != QMessageBox.StandardButton.Yes:
            return False
        try:
            source_archive.archive(plan_documents.source_dir(project.current()), docid)
        except (OSError, ValueError) as exc:
            notices_ui.tell(self.w("plan_doc_err_other", error=exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return False
        self.doc_id = None
        self.reload_documents()
        self.doc_view.set_document(project.current(), None)
        self.show_kind("plan")
        self.show_plan_view()
        self.app.set_status(self.w("plan_doc_deleted", id=docid))
        return True

    def on_page_selected(self, page):
        self.doc_page = page

    def on_page_toggled(self, page, on):
        """«Dans les plans» ticked under a page: a plan made of it; unticked: its plans taken away, asking first where something is drawn on them."""
        if getattr(self.app, "read_only", False):
            self.app.refuse_read_only()
            self.refresh_document_view()
            return
        if on:
            self.create_plan_on(self.doc_id, page)
        else:
            self.remove_plans_on(self.doc_id, page)
        self.refresh_document_view()

    def create_plan_on(self, docid, page, crop=None):
        """A plan of page `page` of document `docid`, saved and exported at once: the next free id, and what the subclass makes of the page (source_for_page) -- or, with `crop` (x, y, w, h), of a frame drawn on it (source_for_frame), that frame its crop (v0.116)."""
        here = project.current()
        try:
            doc = plan_documents.read(here, docid)
            width, height = plan_documents.page_size(here, doc, page)
        except validation.ValidationError as exc:
            notices_ui.tell(self.document_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return None
        pid = self.free_id(self.taken_ids())
        if crop is not None:
            source = self.source_for_frame(pid, docid, page, doc, width, height)
            x, y, w, h = crop
            source["crop"] = {"x": round(x, 2), "y": round(y, 2), "w": round(w, 2), "h": round(h, 2)}
        else:
            source = self.source_for_page(pid, docid, page, doc, width, height)
        try:
            self.write_plan(source)
        except (validation.ValidationError, OSError) as exc:
            notices_ui.tell(str(exc), notifications.CRITICAL, exc=exc, title_key="plan_save_failed_title", source="drawing_tab")
            return None
        self.export(pid, self.w("plan_page_plan_created", id=pid, page=page, doc=docid))
        self.reload_list(select=self.current_id)
        return pid

    def remove_plans_on(self, docid, page):
        """The plans of page `page` of document `docid` taken into the archives -- asking first where something is drawn on them; the page stays ticked where the engineer answers no."""
        return self.archive_plans(self.sources_on(docid, page), page)

    def archive_plans(self, plans, page):
        """The plans `plans` ([(id, source)]) taken into the archives, never deleted -- asking once first where something is drawn on any of them, or where plans of the other kind follow them (detached then); `page` is what the question names. True where they went."""
        if not plans:
            return False
        drawn = [pid for pid, source in plans if self.has_drawing(source)]
        ids = [pid for pid, _source in plans]
        followers = self.followers_of(ids)
        if drawn or followers:
            question = self.w("plan_page_untick_ask", plans=", ".join(drawn), page=page) if drawn else ""
            note = self.followers_note(ids)
            text = "\n\n".join(part for part in (question, note) if part)
            if QMessageBox.question(self, "Woodcore", text) != QMessageBox.StandardButton.Yes:
                return False
        self.detach_followers(ids)
        folder = self.sources_dir()
        for pid in ids:
            if pid == self.current_id:
                self.dirty = False  # what was being drawn on it goes with it
            source_archive.archive(folder, pid)
        self.export("", self.w("plan_page_plans_removed", plans=", ".join(ids)))
        if self.current_id in ids:
            self.load_first()
        else:
            self.reload_list(select=self.current_id)
        return True

    def write_plan(self, source):
        """`source` checked and written as its file -- what a plan made, cropped, calibrated or turned from the document view is."""
        source = dict(source)
        source["schema_version"] = self.domain.version_of(source)   # a plan's and a fire plan's: higher only where it holds a text (issue #43)
        target = self.sources_dir() / f"{source['id']}.json"
        self.domain.check_source(source, target.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return target

    def modify_plans(self, pids, change, done_text):
        """Each plan of `pids` changed by `change(source)` in its file, checked, written, the plans exported -- the plan open saved first where it is one of them and changed, and read again afterwards. True where written."""
        if self.current_id in pids and self.dirty and not self.autosave(ask=True):
            return False
        try:
            for pid in pids:
                path = self.sources_dir() / f"{pid}.json"
                source = json.loads(path.read_text(encoding="utf-8"))
                change(source)
                self.write_plan(source)
        except (validation.ValidationError, OSError, ValueError) as exc:
            notices_ui.tell(str(exc), notifications.CRITICAL, exc=exc, title_key="plan_save_failed_title", source="drawing_tab")
            return False
        self.export(pids[0] if pids else "", done_text)
        if self.current_id in pids:
            self.reload_current()
        else:
            self.reload_list(select=self.current_id if self.view_kind == "plan" else None)
        return True

    def reload_current(self):
        """The plan open read again from its file -- after the document view wrote it -- the view staying what it is."""
        if self.current_id is None:
            return
        path = self.sources_dir() / f"{self.current_id}.json"
        try:
            source = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        self.complete_source(source, self.current_id)
        self.open_source(source, self.current_id, False)
        self.reload_list(select=self.current_id if self.view_kind == "plan" else None)

    def plan_of_page(self, docid, page):
        """The plan a calibration drawn on page `page` is for: the frame chosen on that page (v0.116), else the plan open where it is drawn on that page, else the last of that page's plans; None where none is."""
        plans = [pid for pid, _source in self.sources_on(docid, page)]
        if not plans:
            self.app.set_status(self.w("plan_doc_no_plan_on_page", page=page))
            return None
        chosen = [pid for pid in self.doc_view.selected_frames() if pid in plans]
        if chosen:
            return chosen[-1]
        return self.current_id if self.current_id in plans else plans[-1]

    def on_doc_crop(self, page, rect):
        """A frame drawn on page `page` with «Cadrer» (v0.116, the engineer: «plusieurs cadrages sur une même feuille»): the crop of the page's plan that still shows the whole page -- the one ticking the page made --, and where every plan of the page has a frame already, a NEW plan of that frame, the next free id, saved and exported. Chosen afterwards, so its name and storey are given at once in the right pane."""
        if getattr(self.app, "read_only", False):
            self.app.refuse_read_only()
            return
        x, y, w, h = rect
        crop = {"x": round(x, 2), "y": round(y, 2), "w": round(w, 2), "h": round(h, 2)}
        whole = self.uncropped_on(self.doc_id, page)
        if whole:
            pid = self.current_id if self.current_id in whole else whole[0]
            if not self.modify_plans([pid], lambda source: source.__setitem__("crop", crop), self.w("plan_crop_set", id=pid)):
                return
        else:
            pid = self.create_plan_on(self.doc_id, page, crop=(x, y, w, h))
            if pid is None:
                return
        self.refresh_document_view()
        self.doc_view.select_frames([pid], emit=True)

    def on_doc_frame_edited(self, page, pid, rect):
        """An edge or a corner of the frame of plan `pid` dragged in the document view (v0.116): its crop, written -- a plan of the whole page given a frame so, a fire plan that follows a position plan a crop of its own. Where nothing is written -- a project held read-only (`write_frame_crop` is a writer of woodcore_gui.WRITERS) or the source refused --, the view is drawn again, the frame back where its plan has it."""
        x, y, w, h = rect
        crop = {"x": round(x, 2), "y": round(y, 2), "w": round(w, 2), "h": round(h, 2)}
        if self.write_frame_crop(pid, crop):
            self.refresh_document_view()
            self.doc_view.select_frames([pid], emit=True)
        else:
            self.refresh_document_view()

    def write_frame_crop(self, pid, crop):
        """The crop of plan `pid` written (on_doc_frame_edited) -- True where it was."""
        return self.modify_plans([pid], lambda source: source.__setitem__("crop", crop), self.w("plan_crop_set", id=pid))

    def on_frames_selected(self, plans):
        """The frames chosen in the document view (v0.116): the plan of the one in focus made the plan open -- the plan open before it saved first (autosave) -- and its «Plan» module shown on the right, to be named, described and given a storey at once without the plan being opened; none chosen, the document's own card again."""
        pid = plans[-1] if plans else None
        if pid is not None and pid != self.current_id:
            if not self.confirm_leave():
                self.doc_view.select_frames([self.current_id] if self.frame_module_at is not None else [])
                return
            self.load(pid)
        self.show_frame_module(pid)

    def show_frame_module(self, pid):
        """The plan's «Plan» module moved into the document's right pane for the frame of plan `pid` (the plan open), or -- `pid` None -- put back where it stood in the plan's column, the document's card shown again. The very widgets the plan view edits: what is typed goes into the plan open and is saved as it is left, or as a field is left (on_frame_field_done)."""
        module = getattr(self, "plan_group", None)
        if module is None:
            return
        if pid is None:
            if self.frame_module_at is not None:
                self.frame_layout.removeWidget(module)
                self.properties_layout.insertWidget(self.frame_module_at, module)
                self.frame_module_at = None
                self.update_modules()
            self.frame_box.hide()
            self.doc_card.show()
            self.doc_hint_note.show()
            return
        if self.frame_module_at is None:
            self.frame_module_at = self.properties_layout.indexOf(module)
            self.properties_layout.removeWidget(module)
            self.frame_layout.addWidget(module)
        module.show()
        self.doc_card.hide()
        self.doc_hint_note.hide()
        self.frame_box.show()

    def frame_module_shown(self):
        """Whether the plan's module stands in the document's pane, for a frame chosen."""
        return self.frame_module_at is not None

    def watch_frame_fields(self):
        """Every field of the plan's module saves the plan as it is left while the module stands for a frame (v0.116): the line edits as they are left, a choice in a list as it is made, a box as it is ticked."""
        module = getattr(self, "plan_group", None)
        if module is None:
            return
        for edit in module.findChildren(QLineEdit):
            edit.editingFinished.connect(self.on_frame_field_done)
        for combo in module.findChildren(QComboBox):
            combo.activated.connect(lambda _index: self.on_frame_field_done())
        for box in module.findChildren(QCheckBox):
            box.toggled.connect(lambda _checked: self.on_frame_field_done())

    def on_frame_field_done(self):
        if self.view_kind == "document" and self.frame_module_at is not None and self.dirty:
            QTimer.singleShot(0, self.save_frame_plan)

    def save_frame_plan(self):
        """The plan of the frame chosen saved, quietly, and its frame's label drawn again -- not a renaming, which asks, and is asked as the frame is left (autosave)."""
        if not (self.view_kind == "document" and self.frame_module_at is not None and self.dirty):
            return
        if self.current_id is not None and self.source.get("id") != self.current_id:
            return
        if self.save(quiet=True):
            self.refresh_document_view()
            if self.current_id:
                self.doc_view.select_frames([self.current_id])

    def on_frames_delete(self, plans):
        """Suppr on the frames chosen in the document view (v0.116): their plans archived, never deleted -- asking once first where something is drawn on them (archive_plans)."""
        listed = {pid: source for pid, source in self.sources_on(self.doc_id)}
        chosen = [(pid, listed[pid]) for pid in plans if pid in listed]
        if not chosen:
            return
        pages = ", ".join(str(p) for p in sorted({self.source_page(source) for _pid, source in chosen}))
        if self.archive_plans(chosen, pages):
            self.refresh_document_view()

    def on_doc_calibrated(self, page, points):
        pid = self.plan_of_page(self.doc_id, page)
        if pid is None:
            return
        refused = self.calibration_refused(pid)
        if refused:
            self.app.set_status(refused)
            return
        length = self.ask_length()
        if length is None:
            return
        scale = {"mode": "calibration", "points": [[round(x, 2), round(y, 2)] for x, y in points], "length_m": length}
        self.modify_plans([pid], lambda source: source.__setitem__("scale", scale), self.w("plan_scale_set", id=pid))

    def on_rotate_requested(self, page, delta):
        self.rotate_page(self.doc_id, page, delta)

    def rotate_selected_pages(self, delta):
        pages = self.doc_view.selected_pages() or ([self.doc_page] if self.doc_page else [])
        if not pages:
            self.app.set_status(self.w("plan_doc_no_page"))
            return
        for page in pages:
            self.rotate_page(self.doc_id, page, delta)

    def rotate_current_page(self, delta):
        """The rotation buttons of the plan's «Fond»: the page the plan open is drawn on, turned with it."""
        page = self.current_page()
        if page:
            self.rotate_page(page[0], page[1], delta)

    def rotate_page(self, docid, page, delta):
        """Page `page` of document `docid` turned by `delta` degrees (a quarter turn): the document written, and every plan drawn on that page turned with it (turn_page_drawings) so the drawing stays on the architecture, its sheet the turned page."""
        if getattr(self.app, "read_only", False):
            self.app.refuse_read_only()
            return False
        here = project.current()
        if self.dirty and not self.autosave(ask=True):
            return False
        try:
            turned = self.turn_page_drawings(here, docid, page, delta)
        except plan_documents.DocumentError as exc:
            notices_ui.tell(self.document_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return False
        except (validation.ValidationError, OSError) as exc:
            notices_ui.tell(str(exc), notifications.CRITICAL, exc=exc, title_key="plan_save_failed_title", source="drawing_tab")
            return False
        self.documents.pop(docid, None)
        mine = list(turned.get(self.KIND, []))
        ids = list(turned.get("position", [])) + list(turned.get("fire", []))
        self.export_drawings(self.w("plan_rotated", page=page, plans=", ".join(ids) or "—"), mine[0] if mine else "")
        if self.current_id in mine:
            self.reload_current()
        if self.view_kind == "document" and self.doc_id == docid:
            self.refresh_document_view()
        return True

    def on_layers_changed(self, off):
        """The layers of the document shown switched in the view: written into the document, the plans exported again, and the plan open drawn on it given its background again."""
        if getattr(self.app, "read_only", False):
            return
        here = project.current()
        doc = self.document(self.doc_id)
        if doc is None:
            return
        doc = dict(doc, layers_off=list(off))
        try:
            plan_documents.write(here, doc)
        except (validation.ValidationError, OSError) as exc:
            notices_ui.tell(self.document_error_text(exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return
        self.documents[doc["id"]] = doc
        # the export flattens every page drawn on, seconds on an architect's plan set: run LAYER_EXPORT_MS after the last switch, in a thread, so that switching layers stays instant (v0.116)
        self.layer_export_here = here
        self.layer_timer.start()
        self.app.set_status(self.w("plan_layers_saved", id=doc["id"]))
        current = self.current_page()
        if current and current[0] == doc["id"]:
            self.canvas.reload_background()

    def start_layer_export(self):
        """The export a layer switched asked for, started in its thread -- or, one running, queued after it (_Background.again)."""
        here = self.layer_export_here
        if here is None:
            return
        with _Background.lock:
            if _Background.thread is not None and _Background.thread.is_alive():
                _Background.again = (here, self.layer_notice)
                return
            _Background.thread = threading.Thread(target=_run_layer_export, args=(here, self.layer_notice), daemon=True)
            _Background.thread.start()

    def on_layer_export_done(self, error):
        if error is not None:
            self.app.set_status(self.w("plan_export_failed", id="", error=error))
            return
        self.builder.set_plans(self.builder_records())

    def finish_layer_export(self):
        """Before anything else exports or the tab is left: the export of a layer switched finished -- the one waiting for its time run now, the one running waited for -- so that two exports never write data/ at once, and none asked for is lost when the window closes."""
        pending = self.layer_timer.isActive()
        if pending:
            self.layer_timer.stop()
        thread = _Background.thread
        if thread is not None and thread.is_alive():
            thread.join()
        if pending and self.layer_export_here is not None:
            try:
                plan_pages.export_drawings(self.layer_export_here)
            except (validation.ValidationError, engine.EngineError, OSError) as exc:
                self.app.set_status(self.w("plan_export_failed", id="", error=exc))

    def export_drawings(self, done_text, pid=""):
        """The plans of BOTH kinds exported, here and now (plan_pages.export_drawings): what a page turned, a layer switched or a plan archived needs, since a fire plan may follow the position plan that changed. A failure leaves data/ as it was and says why. True where it ran."""
        self.finish_layer_export()
        try:
            plan_pages.export_drawings(project.current())
        except (validation.ValidationError, engine.EngineError, OSError) as exc:
            notices_ui.tell(self.w("plan_export_failed", id=pid, error=exc), notifications.CRITICAL, exc=exc, source="drawing_tab")
            return False
        self.app.set_status(done_text)
        self.builder.set_plans(self.builder_records())
        return True
