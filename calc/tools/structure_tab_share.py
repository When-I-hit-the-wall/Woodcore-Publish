"""StructureTab's tagging, importing and sharing, the document's content template switched or saved, the sections and objects dropped, and what is shared kept in step -- a mixin of methods moved verbatim out of calc/tools/structure_tab.py (issue #30). StructureTab names it among its bases.
"""

import functools
import shiboken6
from PySide6.QtCore import QFileSystemWatcher, QTimer, Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QInputDialog, QLabel, QMenu, QMessageBox, QPushButton, QSplitter, QVBoxLayout, QWidget
import doc_import  # what is imported from another document, and an object's move (calc/doc_import.py)
import sharing  # a section shared with another document, and no longer (calc/sharing.py)
import doc_templates  # the document saved as a template (calc/doc_templates.py)
import documents  # what each of the three documents is called (calc/documents.py)
import import_dialog  # the questions the tab asks (import_dialog.py)
import project
import settings_dialog  # the words of a template's refusal and of its place (settings_dialog.py)
import structure  # the tree, and everything that writes the structure (calc/structure.py)
import structure_tree  # the tree widget (structure_tree.py)
import sync  # what the documents share, and where each stands (calc/sync.py)
import validation
from structure_tab_view import STRINGS, StructureTabViewMixin  # split out of this module (issue #30): every name it had is still importable from it


# The states of what is shared, from the quietest to the loudest -- calc/sync.py's.
SYNC_RANK = {state: rank for rank, state in enumerate(sync.STATES)}


class StructureTabShareMixin:
    """Methods of structure_tab.StructureTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def on_tag(self):
        if not self.writable():
            return
        node = self.single() or (self.tree.node(self.subject["id"]) if self.subject else None)
        owner = self.file_node(node) if node is not None else None
        if owner is None:
            self.say(self.t("st_off_none"))
            return
        self.write_tag(owner.id)

    def write_tag(self, node_id):
        """The file of `node_id` tagged through structure.tag_section -- every untagged heading and paragraph wrapped in object tags, the document printing as before -- and the tree read again, with the file still chosen. Says how many objects the file gained, or that it had nothing to tag."""
        node = self.tree.node(node_id)
        self.failure = None
        try:
            count = structure.tag_section(project.current(), self.mode(), node_id)
        except self.CAUGHT as exc:
            return self.fail(exc)
        self.update_banner()
        file = node.file if node is not None else node_id
        self.say(self.t("st_tagged", count=count, file=file) if count else self.t("st_tag_nothing", file=file))
        self.reload(select=node_id)
        self.tree.reveal(node_id)
        return True

    def on_import(self):
        if not self.writable():
            return
        answer = self.ask_import()
        if answer is not None:
            self.write_import(*answer)

    def write_import(self, source, items, linked):
        """What was ticked in `source` brought into this document through doc_import.import_items -- linked to its source unless a copy of its own is asked for -- and what arrived chosen, at the bottom of the tree."""
        self.failure = None
        try:
            result = doc_import.import_items(project.current(), self.mode(), source, items, linked=linked)
        except self.CAUGHT as exc:
            return self.fail(exc)
        self.update_banner()
        arrived = [new for _old, new in result.sections] + [f"{result.imported}/{entry[2]}" for entry in result.objects]
        lang = getattr(self.app, "lang", documents.DEFAULT_LANGUAGE)
        self.say(self.t("st_imported", sections=len(result.sections), objects=len(result.objects), source=documents.mode_name(source, lang)))
        self.reload(select=arrived or None)
        for node_id in arrived:
            self.tree.reveal(node_id)
        return True

    def shared_file(self):
        """The file node the section's pane is about -- the one section chosen -- or None, said in the status line."""
        node = self.single() or (self.tree.node(self.subject["id"]) if self.subject else None)
        owner = self.file_node(node) if node is not None else None
        if owner is None:
            self.say(self.t("st_off_none"))
        return owner

    def on_share(self):
        """«Partager avec…»: the other documents of the project asked about, then the file shared into the ones ticked."""
        if not self.writable():
            return
        owner = self.shared_file()
        if owner is None:
            return
        targets = self.ask_share(owner)
        if targets:
            self.write_share(owner.id, targets)

    def on_stop_share(self):
        """«Arrêter le partage»: asked first -- each document keeps its copy, which is independent from then on --, then this copy's tags taken off."""
        if not self.writable():
            return
        owner = self.shared_file()
        if owner is None:
            return
        if self.ask_confirm(self.t("st_stop_share_ask", title=structure_tree.display_title(owner))):
            self.write_stop_share(owner.id)

    def write_share(self, node_id, targets):
        """The file of section `node_id` shared into the documents `targets` through calc/sharing.py's `share` -- the tree read again with the file still chosen, its link mark and its pane saying with whom it is shared. A refusal is said in the banner, by its code. True where it was shared."""
        here, mode = project.current(), self.mode()
        node = self.tree.node(node_id)
        self.failure = None
        try:
            result = sharing.share(here, mode, node_id, targets)
        except self.CAUGHT as exc:
            return self.fail(exc)
        self.update_banner()
        self.stopped_ids().discard(node_id)
        lang = getattr(self.app, "lang", documents.DEFAULT_LANGUAGE)
        self.say(self.t("st_shared_done", file=node.file if node is not None and node.file else node_id, documents=", ".join(documents.mode_name(m, lang) for m in result.modes)))
        self.reload(select=node_id)
        self.tree.reveal(node_id)
        return True

    def write_stop_share(self, node_id):
        """The sharing of section `node_id` stopped through calc/sharing.py's `stop_sharing` -- this copy's shared tags taken off, what lay between them kept -- and the file marked as one whose sharing was stopped: a greyed link mark. True where it was stopped."""
        here, mode = project.current(), self.mode()
        node = self.tree.node(node_id)
        self.failure = None
        try:
            sharing.stop_sharing(here, mode, node_id)
        except self.CAUGHT as exc:
            return self.fail(exc)
        self.update_banner()
        self.stopped_ids().add(node_id)
        self.say(self.t("st_unshared_done", file=node.file if node is not None and node.file else node_id))
        self.reload(select=node_id)
        self.tree.reveal(node_id)
        return True

    def switchable(self):
        """Whether the document shown can switch its content template: a document of a project laid out in three documents (calc/content_switch.py refuses a report written alone)."""
        try:
            here = project.current()
        except project.ProjectError:
            return False
        return bool(getattr(here, "has_modes", False)) and self.mode() in here.modes

    def on_switch_template(self):
        """«Changer de template de fond…»: what a pane holds pending written first, then the comparison asked in its dialog (`ask_switch`); where it wrote something, the tree read again and the page asked for again. Refused, and said, to a project held read-only and to a report written alone."""
        if not self.writable():
            return False
        if not self.switchable():
            self.say(self.t("st_off_switch_single"))
            return False
        self.host.flush()
        result = self.ask_switch()
        if result is None:
            return False
        self.failure = None
        if getattr(result, "changed", False):
            self.say(self.t("st_switch_done", written=len(result.written), archived=len(result.archived)))
        else:
            self.say(self.t("st_switch_nothing"))
        self.reload()
        self.refresh_sync()
        if self.pane_loaded:
            self.request_preview(force=True)
        return True

    def ask_switch(self):
        """The content-switch dialog run on the document shown: its Result where it wrote, None where the engineer cancelled. A method of its own, so that a test answers it without a modal."""
        import content_switch_dialog
        lang = getattr(self.app, "lang", documents.DEFAULT_LANGUAGE)
        dialog = content_switch_dialog.ContentSwitchDialog(self, lang, project.current(), self.mode(), read_only=self.read_only(), convert=self.on_make_absolute)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return dialog.result_

    def on_save_template(self):
        """«Enregistrer comme template de fond…»: the name, the description and the place asked, then the document saved -- the convention, the base or the report alike (doc_templates.ALL_MODES). What a pane holds pending is written first, so that the template is what the engineer sees."""
        self.host.flush()
        answer = self.ask_template()
        if answer is not None:
            self.write_save_template(*answer)

    def template_language(self):
        """The language the document is written in, in the window's words -- the language its template is made in."""
        return self.t("st_lang_" + structure.document_language(project.current(), self.mode()))

    def template_places(self):
        """(place, words, enabled, reason) of the places a template can be saved in: the engineer's own always, the office's where the settings name a folder."""
        lang = getattr(self.app, "lang", documents.DEFAULT_LANGUAGE)
        places = []
        for place in ("user", "office"):
            there = doc_templates.place_dir(place) is not None
            places.append((place, settings_dialog.place_label(lang, place), there, "" if there else self.t("st_template_place_office_off")))
        return places

    def write_save_template(self, name, description, place):
        """The document saved as a document template through doc_templates.save_from_document. A template of that name there already is asked about, and written over -- the old version going to archives/ -- on a yes. A refusal is said in the banner in the window's words, by its code; what is worth knowing about the template that was made (`notes`) is said in a box. True where it was saved."""
        here, mode = project.current(), self.mode()
        self.failure = None
        saved = None
        for overwrite in (False, True):
            try:
                saved = doc_templates.save_from_document(here, mode, name, description, place=place, overwrite=overwrite)
                break
            except self.CAUGHT as exc:
                if not overwrite and getattr(exc, "code", "") == "exists":
                    if self.ask_confirm(self.t("st_template_overwrite_ask", ref=(getattr(exc, "values", {}) or {}).get("ref", name), language=self.template_language())):
                        continue
                    return False        # a no: the template stays as it is, and nothing more is said
                if isinstance(exc, doc_templates.DocTemplateError):
                    self.failure = settings_dialog.doc_error_text(getattr(self.app, "lang", documents.DEFAULT_LANGUAGE), exc)
                    self.update_banner()
                    return False
                return self.fail(exc, reload=False)
        self.update_banner()
        self.say(self.t("st_template_saved", name=name, folder=saved.folder))
        notes = [self.template_note(note) for note in saved.notes]
        if notes:
            self.tell(self.t("st_template_notes_title"), "  ".join(notes))
        return True

    def template_note(self, note):
        """What is worth knowing about a template just saved (an `engine.Note`) in the window's words: the sentence of its code, its values written in; the English sentence where the code has none."""
        code = getattr(note, "code", "")
        key = "st_template_note_" + code.removeprefix("template_")
        if not code.startswith("template_") or key not in STRINGS["en"]:
            return str(note)
        args = dict(getattr(note, "args", {}) or {})
        files = args.get("files")
        if isinstance(files, dict):
            args["files"] = ", ".join(files)
        return self.format(key, args)

    def on_dropped(self, ids, target, where):
        """A drop in the tree: the model is asked to move what was dragged, after the signal has finished -- the tree is filled again by it."""
        self.drops.append((list(ids), target, where))
        QTimer.singleShot(0, functools.partial(self.deferred, functools.partial(self.drop_nodes, list(ids), target, where)))

    def top_nodes(self, nodes):
        """`nodes` without any whose chapter or section is among them too: moving the chapter moves it."""
        ids = {node.id for node in nodes}
        out = []
        for node in nodes:
            parent, hidden = self.tree.node(node.parent) if node.parent else None, False
            while parent is not None:
                if parent.id in ids:
                    hidden = True
                    break
                parent = self.tree.node(parent.parent) if parent.parent else None
            if not hidden:
                out.append(node)
        return out

    def drop_nodes(self, ids, target_id, where):
        """What a drop means: **sections and chapters** dropped on a row go where `where` says -- above or below a section or a chapter as one of its siblings, on a chapter at its end, on an object or a heading after its section, on nothing at the end -- and **objects** go into the file of the row dropped on, above or below an object or at the end of a section. A refusal -- by the model or by the tab -- is said in the banner and the tree is read again. True where something moved."""
        if not self.writable():
            return False
        nodes = [self.tree.node(i) for i in ids if self.tree.node(i) is not None]
        target = self.tree.node(target_id) if target_id else None
        if not nodes:
            return False
        if any(node.kind == "heading" for node in nodes):
            return self.reload_after(self.refuse("st_drop_untagged"))
        sections = [node for node in nodes if node.kind in ("file", "group")]
        objects = [node for node in nodes if node.kind == "object"]
        if sections and objects:
            return self.reload_after(self.refuse("st_drop_mixed"))
        self.failure = None
        try:
            moved = self.drop_sections(self.top_nodes(sections), target, where) if sections else self.drop_objects(objects, target, where)
        except self.CAUGHT as exc:
            self.failure = self.why(exc)
            self.update_banner()
            self.reload()
            return False
        self.update_banner()
        if moved:
            self.say(self.t("st_moved_many", count=len(moved)) if len(moved) > 1 else self.t("st_moved_one", id=moved[0].split("/")[-1]))
        self.reload(select=moved or None)
        for node_id in moved:
            self.tree.reveal(node_id)
        return bool(moved)

    def reload_after(self, value):
        self.reload()
        return value

    def drop_sections(self, nodes, target, where):
        """Sections and chapters `nodes` moved to where a drop on `target` says: as the siblings of a section or chapter above or below it, inside a chapter dropped on, after the section an object or heading belongs to, at the end of the document on nothing. Every move asks the model for the place it has *now*, so that several land one after the other. Returns the ids moved."""
        mode = self.mode()
        place = target
        if place is not None and place.kind in ("object", "heading"):
            place, where = self.file_node(place), "below"
        if place is not None and place.kind == "file" and where == "on":
            where = "below"
        if place is None:
            parent, anchor, after = None, None, True
        elif place.kind == "group" and where == "on":
            parent, anchor, after = place.id, None, True
        else:
            parent, anchor, after = (place.parent or None), place.id, where != "above"
        done = []
        for node in nodes:
            if place is not None and node.id == place.id:
                continue
            position = None
            if anchor is not None:
                rest = [i for i in self.sibling_ids(parent) if i != node.id]
                if anchor not in rest:
                    continue
                position = rest.index(anchor) + (1 if after else 0)
            self.nodes = structure.tree(project.current(), mode)
            if not self.write_move(node.id, parent, position):
                raise ValueError(self.failure or "")
            done.append(node.id)
            if after and anchor is not None:
                anchor = node.id
        return done

    def drop_objects(self, nodes, target, where):
        """Objects `nodes` moved into the file of `target`: above or below an object, or at the end of the file where a section or a heading is dropped on. Returns the ids they have in their new files."""
        here, mode = project.current(), self.mode()
        if target is None:
            raise ValueError(self.t("st_drop_nowhere"))
        if target.kind == "group":
            raise ValueError(self.t("st_drop_object_on_group"))
        owner = self.file_node(target)
        if owner is None:
            raise ValueError(self.t("st_drop_nowhere"))
        before = after = None
        reference = None
        if target.kind == "object":
            reference = target.object_id
            if where == "above":
                before = reference
            else:
                after = reference
        done = []
        for node in nodes:
            if target.kind == "object" and node.id == target.id:
                continue
            doc_import.move_object(here, mode, node.parent, node.object_id, owner.id, before=before, after=after)
            done.append(f"{owner.id}/{node.object_id}")
            if after is not None:
                after = node.object_id
        return done

    def refresh_sync(self):
        """The state of everything the document shares worked out again (calc/sync.py `status`, a tenth of a second) and the tree and the buttons made to follow it. Settling -- recording that copies found equal are in step -- writes records, which a project opened read-only does not."""
        if not shiboken6.isValid(self):
            return None
        try:
            status = sync.status(project.current(), self.mode(), settle=not self.read_only())
        except (sync.SyncError, validation.ValidationError, project.ProjectError, OSError):
            status = None
        self.apply_sync_status(status)
        return status

    def apply_sync_status(self, status):
        """**The hook of the synchronisation**: the rows coloured and marked by `status` -- a `sync.Status`, None for nothing -- orange where another document changed what this one shares and has not imported it, red where both changed, grey where the engineer chose to ignore it -- and the three buttons and their count made to follow. Called after every write, every import and every change on disk."""
        self.sync_status = status
        self.tree.set_sync(self.sync_state, self.sync_tip)
        self.update_buttons()

    def sync_state(self, node):
        """A node's state against the other documents -- `incoming`, `conflict`, `ignored`, `local`, `problem` or `in_sync` -- None where it shares nothing: an object by the block it stands in and its own id, a section by the worst of its blocks, a chapter by the worst of its sections."""
        status = self.sync_status
        if status is None:
            return None
        if node.kind == "object":
            if not node.shared:
                return None
            found = status.item(sync.item_key(node.shared, node.object_id))
            return found.state if found is not None else None
        if node.kind == "file":
            found = status.file(node.file) if node.file else None
            return found.state if found is not None else None
        if node.kind == "group":
            states = [self.sync_state(child) for child in structure.flatten(node.children) if child.kind == "file"]
            states = [state for state in states if state in ("incoming", "conflict", "problem")]
            return max(states, key=SYNC_RANK.get) if states else None
        return None

    def sync_modes(self, node):
        """The documents that make a node's state what it is, as codes: the ones that changed an object, the ones involved in the blocks of a section, the ones of its sections for a chapter."""
        status = self.sync_status
        if status is None:
            return []
        modes = []
        if node.kind == "object" and node.shared:
            found = status.item(sync.item_key(node.shared, node.object_id))
            modes = list(found.others) if found is not None else []
        elif node.kind == "file":
            found = status.file(node.file) if node.file else None
            for shared_id in (found.blocks if found is not None else ()):
                block = status.block(shared_id)
                modes += list(block.involved) if block is not None else []
        elif node.kind == "group":
            for child in structure.flatten(node.children):
                if child.kind == "file":
                    modes += self.sync_modes(child)
        return list(dict.fromkeys(modes))

    def sync_documents(self, node):
        """`sync_modes` as the names a person reads, in the window's language."""
        lang = getattr(self.app, "lang", documents.DEFAULT_LANGUAGE)
        return [documents.mode_name(mode, lang) for mode in self.sync_modes(node)]

    def sync_tip(self, node):
        """What a row's sync mark says: which documents changed it and what «Importer les modifications» does with it."""
        state = self.sync_state(node)
        key = {"incoming": "st_sync_tip_incoming", "conflict": "st_sync_tip_conflict", "ignored": "st_sync_tip_ignored",
               "problem": "st_sync_tip_problem", "local": "st_sync_tip_local"}.get(state)
        return self.t(key, documents=", ".join(self.sync_documents(node))) if key else ""

    def sync_keys(self, nodes):
        """The shared items the rows `nodes` stand for, as calc/sync.py names them: «<shared id>» for each block of a section's file -- a chapter's sections' --, «<shared id>/<object id>» for an object in a block."""
        keys = []
        for node in nodes:
            if node.kind == "file":
                keys += list(node.shared_ids)
            elif node.kind == "group":
                for child in structure.flatten(node.children):
                    if child.kind == "file":
                        keys += list(child.shared_ids)
            elif node.kind == "object" and node.shared:
                keys.append(sync.item_key(node.shared, node.object_id))
        return list(dict.fromkeys(keys))

    def conflict_keys(self, status, keys):
        """The conflicts the engineer is asked about: those among `keys` -- among every conflict where `keys` is None -- **at the most specific level**. A block whose objects conflict is not asked about as a block: its objects are, and a choice made for one object does not decide another. A block is asked about where its own text conflicts, or where none of its objects does."""
        pool = list(status.conflicts) if keys is None else [key for key in keys if status.state_of(key) == "conflict"]
        asked = []
        for key in pool:
            shared_id, object_id = sync.split_key(key)
            if object_id is None:
                block = status.block(shared_id)
                under = [o for o in (block.objects if block is not None else ()) if status.state_of(sync.item_key(shared_id, o.id)) == "conflict"]
                if under and block.text_state != "conflict":
                    continue
            asked.append(key)
        return asked

    def ask_choice(self, key, found):
        """Which version of `key` -- a shared block or object changed here and in another document -- to keep: `mine`, `theirs` (the newest) or a document's code, None where the engineer cancels."""
        lang = getattr(self.app, "lang", documents.DEFAULT_LANGUAGE)
        sources = list(getattr(found, "sources", ()) or ())
        if not sources:       # a block's own text: the documents that hold a copy of it
            sources = [mode for mode in (getattr(found, "involved", ()) or ()) if mode != self.mode()]
        newest = sources[0] if sources else None
        options = [("mine", self.t("st_choice_mine", mine=documents.mode_name(self.mode(), lang)))]
        if newest is not None:
            options.append(("theirs", self.t("st_choice_theirs", document=documents.mode_name(newest, lang))))
        options += [(mode, self.t("st_choice_from", document=documents.mode_name(mode, lang))) for mode in sources[1:]]
        dialog = import_dialog.ChoiceDialog(self, self.t, key, ", ".join(documents.mode_name(mode, lang) for mode in sources), options)
        return dialog.chosen() if dialog.exec() == QDialog.DialogCode.Accepted else None

    def on_sync_import(self):
        if not self.writable():
            return
        chosen = self.selection()
        keys = self.sync_keys(chosen) if chosen else None
        self.write_sync_import(keys)

    def write_sync_import(self, keys=None):
        """What the other documents changed taken into this one, **between the tags only** (calc/sync.py `import_changes`): `keys` -- None for everything incoming and not ignored. For each conflict among what is asked for the engineer is asked which version to keep. True where the import went through."""
        here, mode = project.current(), self.mode()
        status = self.refresh_sync()
        if status is None:
            return False
        choices = {}
        for key in self.conflict_keys(status, keys):
            choice = self.ask_choice(key, status.item(key))
            if choice is None:
                return False
            choices[key] = choice
        self.failure = None
        try:
            result = sync.import_changes(here, mode, keys, choices)
        except self.CAUGHT + (sync.SyncError,) as exc:
            return self.fail(exc, reload=False)
        self.update_banner()
        if result.imported:
            self.say(self.t("st_sync_imported", count=len(result.imported), items=", ".join(result.imported)))
        elif result.kept:
            self.say(self.t("st_sync_kept", count=len(result.kept)))
        elif result.unchanged:
            self.say(self.t("st_sync_unchanged", items=", ".join(result.unchanged)))
        else:
            self.say(self.t("st_sync_off_incoming"))
        self.reload()
        self.refresh_sync()
        return True

    def on_sync_ignore(self):
        if self.writable():
            self.write_sync_flag(self.sync_keys(self.selection()), True)

    def on_sync_reactivate(self):
        if self.writable():
            self.write_sync_flag(self.sync_keys(self.selection()), False)

    def write_sync_flag(self, keys, ignored):
        """«Ignorer» (`ignored`) or «Réactiver» for `keys` -- remembered, per document, until it is taken off -- and the tree and the buttons made to follow."""
        if not keys:
            return self.refuse("st_sync_off_selection")
        self.failure = None
        try:
            result = (sync.ignore if ignored else sync.reactivate)(project.current(), self.mode(), keys)
        except self.CAUGHT + (sync.SyncError,) as exc:
            return self.fail(exc, reload=False)
        self.update_banner()
        if result.changed:
            self.say(self.t("st_sync_ignored_done" if ignored else "st_sync_reactivated_done", items=", ".join(result.changed)))
        self.refresh_sync()
        return True
