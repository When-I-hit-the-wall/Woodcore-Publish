"""MemberCheckTab's list of checks on the left, what is calculated and shown with its command, and its buttons -- new, duplicate, revert, delete, save, export -- a mixin of methods moved verbatim out of calc/tools/member_check_tab.py (issue #30). MemberCheckTab names it among its bases.
"""

import json
import re
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSplitter, QVBoxLayout, QWidget,
)
import build_reference as ref
import cards  # the form and what is read off it in cards, after the website (cards.py)
import autosave  # saving without a question, and what is never saved without the engineer (autosave.py, v0.117)
import grouped_list
import project  # where the project this tab works on is (calc/project.py)
import richtext  # the call coloured as the site's code, «Copié ✓» once copied (richtext.py)
import source_archive  # «Supprimer» archives (source_archive.py)
import structure_preview  # the lines every snippet starts with: the project's conf, the engine, the language
import validation
from domains import connector, member_check
import display_options  # the level -1 «Sélection manuelle» (issue #20)
from member_check_tab_words import STRINGS, _check_strings  # split out of this module (issue #30): every name it had is still importable from it


NEW_ROW = "<new>"


ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$")


def next_free_id(taken, prefix="Z_"):
    """The first free <prefix><nn>: «Z_01» for a tension (Zug), «DR-01» for a compression (Druck), as the connectors' are numbered SD_01. `taken` is every ID of every kind -- the folder is shared."""
    lower = {t.lower() for t in taken}
    index = 1
    while True:
        candidate = "%s%02d" % (prefix, index)
        if candidate.lower() not in lower:
            return candidate
        index += 1


class MemberCheckActionsMixin:
    """Methods of member_check_tab.MemberCheckTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def build_list(self):
        box = QWidget()
        column = QVBoxLayout(box)
        self.list = grouped_list.GroupedList(STRINGS.get(self.app.lang, STRINGS["fr"]), lang=self.app.lang)
        self.archive = source_archive.Actions(self, lambda: self.sources_dir(), self.export, lambda select: self.reload_list(select), self._after_archive)
        self.archive.connect()
        column.addWidget(grouped_list.title_row(self.heading(self.t(self.LIST_KEY)), self.list))
        self.list.setIconSize(self.app.mark_size)
        self.list.currentIdChanged.connect(self.on_list_change)
        self.list.moved.connect(self.on_moved)
        self.list.foldersChanged.connect(self.on_folders_changed)
        self.list.attach_order(self.KEY, self.app.list_store)   # the order the engineer gives the list by drag and drop, kept in Woodcore-Datei/lists.json (calc/list_order.py, issue #15)
        self.list.reordered.connect(lambda: self.reload_list(self.current_id))
        column.addWidget(self.list, 1)
        self.empty_hint = cards.note(self.t(self.EMPTY_KEY))
        column.addWidget(self.empty_hint)
        row = QHBoxLayout()
        for key, slot in (("mc_new", self.new), ("mc_duplicate", self.duplicate), ("mc_delete", self.delete)):
            button = QPushButton(self.t(key))
            button.clicked.connect(slot)
            row.addWidget(button)
        column.addLayout(row)
        return box

    def _group_of(self, cid):
        """The folder a check is filed in, read off its own source -- the field, never a directory (grouped_list.py)."""
        try:
            source = json.loads((self.sources_dir() / ("%s.json" % cid)).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return grouped_list.ROOT_GROUP
        return grouped_list.group_of(source)

    def reload_list(self, select=None):
        self.loading = True
        self.ids = self._own_ids()
        entries = [{"id": cid, "text": cid, "group": self._group_of(cid)} for cid in self.ids]
        if self.current_id is None:      # the draft nobody has saved yet, at the root where it can be seen
            draft = (self.source or {}).get("id") or "?"
            entries.append({"id": NEW_ROW, "text": f"{draft} {self.t('mc_new_item')}", "group": grouped_list.ROOT_GROUP})
        target = select if select in self.ids else (NEW_ROW if self.current_id is None else None)
        self.list.set_entries(entries, self.empty_folders, target,
                              archived=self._archived_of_kind())
        self.empty_folders = self.list.empty_folders()
        self.app.save_folder_settings(self.KEY, self.empty_folders)
        self.empty_hint.setVisible(not self.ids)
        self.loading = False
        self.update_list_marker()

    def on_folders_changed(self):
        """A folder made, renamed or removed in the list: what the widget now holds is what the tab keeps -- never the tab's own copy, taken before the new folder was added (the connectors' lesson)."""
        self.empty_folders = self.list.empty_folders()
        self.reload_list(select=self.current_id)

    def update_list_marker(self):
        """A dot beside the check being edited while it has unsaved changes, on every row a dot or a blank of the same size."""
        for cid in self.list.ids():
            mine = cid == self.current_id or (self.current_id is None and cid == NEW_ROW)
            self.list.set_mark(cid, self.app.dirty_mark(mine and self.dirty))
        self.app.update_tab_marks()

    def on_list_change(self, cid):
        if self.loading or not cid or cid not in self.ids:
            return
        if not self.confirm_leave():
            self.loading = True
            self.list.select(self.current_id) if self.current_id in self.ids else None
            self.loading = False
            return
        self.load(cid)
        if NEW_ROW in self.list.ids():
            self.reload_list(cid)         # the draft given up leaves the list

    def on_moved(self, ids, group):
        """A drop wrote a folder: the field goes into each source, the checks are exported, the list is rebuilt from the files."""
        if not self.confirm_leave():
            self.reload_list(self.current_id)
            return
        for cid in ids:
            if cid == NEW_ROW:
                continue                  # a draft has no file to write the field into
            path = self.sources_dir() / ("%s.json" % cid)
            try:
                source = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if group:
                source["group"] = group
            else:
                source.pop("group", None)
            path.write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            if cid == self.current_id:
                if group:
                    self.source["group"] = group      # the draft takes the folder too, or its next save would put the check back where it was
                else:
                    self.source.pop("group", None)
        self.export(self.t("mc_moved", count=len(ids), group=group or "—"))
        self.reload_list(self.current_id)

    def load(self, cid):
        path = self.sources_dir() / ("%s.json" % cid)
        try:
            source = self.DOMAIN.read_source(path)
        except validation.ValidationError:
            source = json.loads(path.read_text(encoding="utf-8"))   # a source the checks refuse is still opened, so it can be repaired here
        self.source = source
        self.current_id = cid
        self.dirty = False
        self.fill_form()
        self.refresh()

    def options(self):
        """The options of the command as the engineer set them: the level (None: the report's own), the member line (`"none"` or 0 to 3, 1 being the command's own), the description, the title (None: the command's own, False: `none`, or the text) and the unit of the utilisation (None: a ratio, or `"%"`)."""
        state = self.title_box.currentData()
        title = False if state == "none" else ((self.title_text.text() or None) if state == "text" else None)
        level = self.level_box.level()
        return {"level": None if level == "auto" else int(level), "member": self.member_box.currentData(),
                "description": self.description_box.isChecked(), "title": title, "unit": self.unit_box.currentData(),
                "shown": self.level_box.picked() if level == display_options.SELECTION else None}

    def draft_options(self):
        """The options as `member_check.draft_typst` takes them: its member line is None for none, the level otherwise."""
        o = self.options()
        return {"level": o["level"], "member_level": None if o["member"] == "none" else o["member"],
                "description": o["description"], "title": o["title"], "unit": o["unit"], "shown": o["shown"]}

    def call_options(self):
        """The options as `build_reference.call_show_check_member` takes them: its member line is False for none, None where it is the command's own 1."""
        o = self.options()
        member = False if o["member"] == "none" else (None if o["member"] == 1 else o["member"])
        return {"level": o["level"], "member_level": member, "description": o["description"], "title": o["title"], "unit": o["unit"], "shown": o["shown"]}

    def command_text(self):
        return ref.call_show_check_member(self.draft()["id"], **self.call_options())

    def on_option(self, *_args):
        if self.loading:
            return
        self.title_text.setEnabled(self.title_box.currentData() == "text")
        self.description_box.setEnabled(self.member_box.currentData() not in ("none", 0))
        self.member_box.setEnabled(self.level_box.level() != display_options.SELECTION)   # at -1 the one list is the member's too, its level giving way (spec D-11)
        self.fill_results()      # the unit of the utilisation shows in the verdict
        self.fill_command()

    def refresh(self, preview=True):
        """The draft read: resolved against the positions, its warnings said, the results and the command written -- and the page asked for again (`preview`), which is nothing while the preview is closed."""
        source = self.draft()
        self.record, self.reason = None, ""
        warnings = []
        try:
            self.DOMAIN.check_source(source)
            self.record = self.resolve_draft(source)
            for note in self.record.get("warnings") or []:
                warnings.append(self.app.note_text(note))   # the record's own words, in the window's language: «ne peut pas être vérifiée — …»
            if not self.record.get("calculable", True):
                self.reason = self.t("mc_no_calc", reason=self.tl(self.record.get("reason") or ""))
        except (validation.ValidationError, ValueError, KeyError, TypeError) as exc:
            self.reason = self.t("mc_invalid", error=str(exc))
            warnings.append(self.reason)
        self.message.setText("<br>".join(richtext.prose_html(w) for w in warnings))
        self.message.setVisible(bool(warnings))
        self.description_box.setEnabled(self.member_box.currentData() not in ("none", 0))
        # what -1 offers: the lines this check prints (D-15), its verdicts among them (issue #58)
        self.level_box.set_keys(self.shown_keys_of(self.record) if self.record is not None else [])
        self.fill_results()
        self.fill_command()
        self.update_list_marker()
        if preview:
            self.request_preview()

    def shown_keys_of(self, record):
        """What -1 «Sélection manuelle» offers for the record: the lines the check prints, a verdict by its symbol (issue #58)."""
        return member_check.shown_choices(record)

    def fill_command(self):
        """The «Affichage» view told what the check is now: its call, whether it is saved, why it cannot be computed -- and the page asked for again, which is nothing outside «Affichage»."""
        self.display.set_project(project.current(), self.app.current_document())
        self.display.set_entries(self.display_entries())

    def preview_source(self):
        """The Typst the pane compiles: the lines every snippet starts with -- the project's `conf`, the engine, the document and its language -- and the draft's own call, its values written into it, so nothing needs saving first. None where there is nothing to compile."""
        if self.record is None or not self.record.get("calculable"):
            return None      # nothing to print: the pane says why instead (request_preview)
        body = member_check.draft_typst(self.record, **self.draft_options())
        if not body:
            return None
        here = project.current()
        return "\n".join(structure_preview.header(here, self.app.current_document())) + "\n\n" + body + "\n"

    def request_preview(self):
        """Asks for the page of the draft -- compiled a moment from now, the newest request winning, in «Affichage» alone (display_view.DisplayView.refresh); Typst's own message stays in the pane's banner. Nothing is asked before the tab has been shown."""
        if not self.live or self.view != "display":
            return
        try:
            if not self.display.active:
                self.display.activate(True)     # shown in «Affichage»: the page is asked for from now on
            else:
                self.display.refresh()
        except Exception as exc:  # broad: a draft the engine cannot write out is said, never raised through a slot
            self.message.setText(richtext.prose_html(self.t("mc_invalid", error=str(exc))))
            self.message.setVisible(True)

    def on_shown(self):
        """The tab brought to the front: the positions are read again -- one added or changed in «Positions» is offered at once --, and the page is compiled for the first time."""
        self.live = True
        self._positions_key = None             # the positions are read again
        dirty = self.dirty
        self.source = self.draft()
        self.reload_list(self.current_id)      # a check made, moved or archived in another tab of the same folder
        self.fill_form()
        self.dirty = dirty
        self.refresh()

    def showEvent(self, event):
        super().showEvent(event)
        if not self.live:
            self.live = True
            self.panes.show(self.view == "display")

    def stop(self):
        self.pane.stop()

    def new(self):
        if not self.confirm_leave():
            return
        self.source = self.make_source()
        self.current_id = None
        self.dirty = True
        self.fill_form()
        self.refresh()
        self.reload_list()

    def duplicate(self):
        if not self.confirm_leave():
            return
        source = self.draft()
        source["id"] = next_free_id(self._taken(), self.ID_PREFIX)
        source.pop("name", None)
        self.source = source
        self.current_id = None
        self.dirty = True
        self.fill_form()
        self.refresh()
        self.reload_list()

    def revert(self):
        if self.current_id:
            self.load(self.current_id)
        else:
            self.new()

    def delete(self):
        """«Supprimer»: what is selected goes to «Archives», its ID removed (source_archive.py) -- or, an archived entry selected, is deleted for good. A check never saved is simply discarded, as in the other editor tabs."""
        if self.archive.delete():
            return
        self.dirty = False
        self.reload_list()
        if self.ids:
            self.load(self.ids[0])
            self.reload_list(self.ids[0])
        else:
            self.new()

    def _after_archive(self):
        """The check the form showed was archived: a new one opens, as deleting always did here."""
        self.reload_list()
        self.new()

    def fail(self, message):
        return autosave.refuse(self, self.t(self.KEY), message)

    def save(self):
        source = self.draft()
        cid = source["id"]
        if not ID_PATTERN.match(cid or ""):
            return self.fail(self.t("mc_taken", id=cid))
        taken = {t.lower() for t in self._taken()} - ({self.current_id.lower()} if self.current_id else set())
        if cid.lower() in taken:
            return self.fail(self.t("mc_taken", id=cid))
        if self.current_id and self.current_id != cid:
            if not autosave.ask_rename(self, self.t("mc_rename_title"), self.t("mc_rename", old=self.current_id, new=cid)):
                return False
        try:
            self.DOMAIN.check_source(source)
        except (validation.ValidationError, ValueError) as exc:
            return self.fail(self.t("mc_invalid", error=str(exc)))
        folder = self.sources_dir()
        folder.mkdir(parents=True, exist_ok=True)
        if self.current_id and self.current_id != cid:
            (folder / ("%s.json" % self.current_id)).unlink(missing_ok=True)
        (folder / ("%s.json" % cid)).write_text(json.dumps(source, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.source = source
        self.current_id = cid
        self.dirty = False
        self.export(self.t("mc_saved", id=cid))
        self.reload_list(select=cid)
        self.fill_command()
        return True

    def export(self, done):
        try:
            self.DOMAIN.export(project.current())
        except Exception as exc:  # broad: the exporter's own message is what helps
            self.app.set_status(self.t("mc_export_failed", error=str(exc)))
            return
        self.app.set_status(done)

    def confirm_leave(self):
        return autosave.confirm(self.app, self, self.t("mc_unsaved_title"), self.t("mc_unsaved", id=self.identity.id.text().strip() or "?"))   # saved without a question where it can be, else the one question (autosave.py, v0.117)
