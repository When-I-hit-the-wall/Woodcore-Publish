"""StructureTab's writes -- why one was refused, a section's state, title and place, the objects of a section added, removed, restored -- a mixin of methods moved verbatim out of calc/tools/structure_tab.py (issue #30). StructureTab names it among its bases.
"""

import functools
from pathlib import Path
import shiboken6
from PySide6.QtCore import QFileSystemWatcher, QTimer, Qt
import documents  # what each of the three documents is called (calc/documents.py)
import project
import removed_objects  # the objects taken out of the document, kept where they stood (calc/removed_objects.py)
import structure  # the tree, and everything that writes the structure (calc/structure.py)
import structure_tree  # the tree widget (structure_tree.py)
import structure_words  # the words (structure_words.py)
import sync  # what the documents share, and where each stands (calc/sync.py)
import typst_objects  # the objects of a file, and the writing of one (calc/typst_objects.py)
import typst_paths
import validation
from structure_tab_view import STRINGS, StructureTabViewMixin  # split out of this module (issue #30): every name it had is still importable from it


# The codes a refusal can carry that have a sentence of their own.
WHY = {code: "st_why_" + code for code in structure_words.CODES}


class _Safe(dict):
    def __missing__(self, key):
        return "?"


def _lines(text):
    import re
    return re.findall(r"[^\r\n]*(?:\r\n|\r|\n)|[^\r\n]+", text)


def shared_block_text(text, shared_id):
    """The text between the two tags of shared block `shared_id` in a file's text, line endings as the file has them -- None where it holds none. What calc/sync.py is told an edit started from."""
    blocks = structure.pair_tags(text)[0]
    block = next((b for b in blocks if b.kind == "shared" and b.id == shared_id), None)
    if block is None:
        return None
    return "".join(_lines(text)[block.start + 1:block.end])


class StructureTabWriteMixin:
    """Methods of structure_tab.StructureTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def format(self, key, values):
        """The sentence `key` with `values` -- a list joined, a missing value a «?» -- in the window's language."""
        table = STRINGS.get(getattr(self.app, "lang", "fr"), STRINGS["en"])
        filled = {name: (", ".join(str(v) for v in value) if isinstance(value, (list, tuple)) else value) for name, value in values.items()}
        return table[key].format_map(_Safe(filled))

    def why(self, exc):
        """A refusal in the window's own words, by its code; the sentence it carries where it has none -- a disk that failed, a file that could not be read."""
        code = getattr(exc, "code", "")
        values = dict(getattr(exc, "values", {}) or {})
        if code == "id_exists" and values.get("file"):
            key = "st_why_id_exists_object"
        elif code in WHY:
            key = WHY[code]
        else:
            return self.t("st_write_failed", error=exc) if isinstance(exc, OSError) else str(exc)
        if code == "shared" and not values.get("shared_with"):
            values["shared_with"] = self.t("st_by_tags")
        if "shared_ids" in values and "shared_id" not in values:       # sharing.share says the blocks the target holds, doc_import the one: the sentence names them either way
            values["shared_id"] = values["shared_ids"]
        lang = getattr(self.app, "lang", documents.DEFAULT_LANGUAGE)
        for name in ("mode", "shared_with", "modes", "documents", "others"):
            if name in values and values[name] != self.t("st_by_tags"):       # a document is said by its name, not by its code
                named = [documents.mode_name(mode, lang) if mode in project.MODES else mode for mode in (values[name] if isinstance(values[name], (list, tuple)) else [values[name]])]
                values[name] = named if isinstance(values[name], (list, tuple)) else named[0]
        if code == "tags_unreadable" and values.get("file"):
            values["file"] = Path(str(values["file"])).name
        return self.format(key, values)

    def fail(self, exc, reload=True):
        """A write that failed or was refused: the banner says why, in the window's words, and the tree is read again from the files -- a box ticked for nothing is not left ticked."""
        self.failure = self.why(exc)
        self.update_banner()
        if reload:
            self.reload()
        return False

    def refuse(self, key, **values):
        """A refusal of the tab's own, said in the banner; nothing changes."""
        self.failure = self.t(key, **values)
        self.update_banner()
        return False

    def succeeded(self):
        """The last write went through: its refusal is no longer said."""
        self.failure = None
        self.update_banner()

    def on_toggled(self, node_id, enabled):
        """A box ticked or cleared, in the tree. Written after the signal that said so has finished: the tree is filled again by the write, and a tree cleared from inside its own `itemChanged` is one that crashes."""
        QTimer.singleShot(0, functools.partial(self.apply_toggle, node_id, enabled))

    def apply_toggle(self, node_id, enabled):
        if not shiboken6.isValid(self):
            return      # the window was built again between the click and now
        if not self.write_enabled(node_id, enabled):
            self.reload()       # a box ticked for nothing is not left ticked

    def write_enabled(self, node_id, enabled, refresh_pane=True):
        """Section `node_id` switched on or off through structure.set_enabled -- the tree read again, the page asked for, the right pane made again where it shows this node (`refresh_pane`; not where it is the pane that asked). True where it was written or already so; False where it was refused or failed, which the banner then says."""
        here, mode = project.current(), self.mode()
        self.failure = None
        try:
            changed = structure.set_enabled(here, mode, node_id, enabled)
        except self.CAUGHT as exc:
            return self.fail(exc)
        self.update_banner()
        node = self.tree.node(node_id)
        shown = refresh_pane and self.subject is not None and self.subject.get("id") == node_id
        self.reload(select=self.tree.selected_ids() or node_id, pane=shown)
        if changed:
            self.say(self.t("st_done_enabled" if enabled else "st_done_disabled", title=structure_tree.display_title(node) if node else node_id))
            self.request_preview()
        return True

    def write_title(self, node_id, title, language=None, refresh_pane=True):
        """The title of `node_id` rewritten through structure.set_title, in the document's language -- a chapter's kept in all three and a file's in the one it is written in; `language` names the one of a chapter to write. Same return as `write_enabled`."""
        here, mode = project.current(), self.mode()
        self.failure = None
        before = self.block_snapshot(node_id)
        try:
            changed = structure.set_title(here, mode, node_id, language or structure.document_language(here, mode), title)
        except self.CAUGHT as exc:
            return self.fail(exc)
        self.update_banner()
        if changed and before:      # a title that stands in a block shared with another document is an edit of that block: the others see it as incoming
            after = self.block_snapshot(node_id)
            for shared_id, was in before.items():
                if was is not None and after.get(shared_id) != was:
                    self.record_edit(shared_id, was)
        shown = refresh_pane and self.subject is not None and self.subject.get("id") == node_id
        self.reload(select=self.tree.selected_ids() or node_id, pane=shown)
        if changed:
            self.say(self.t("st_done_title", id=node_id, title=title))
            self.request_preview()
        return True

    def block_snapshot(self, node_id):
        """{shared id: the text between its tags} of the file that `node_id` stands in, as it is now -- what a write to the file is compared with to tell calc/sync.py what changed. Empty where the file shares nothing or cannot be read."""
        node = self.tree.node(node_id)
        owner = self.file_node(node) if node is not None else None
        if owner is None or not owner.shared_ids:
            return {}
        text = self.read_text(owner)
        if text is None:
            return {}
        return {shared_id: shared_block_text(text, shared_id) for shared_id in owner.shared_ids}

    def write_node_state(self, node_id, state):
        """What the pane of a section or a chapter says -- its title, its titles, whether it is printed -- written where it differs from what the pane was loaded with. True where everything that differed was written."""
        subject = self.subject
        ok = True
        if subject["kind"] == "chapter":
            for lang in structure.LANGUAGES:
                new = (state.titles.get(lang) or "").strip()
                if new and new != (subject["titles"].get(lang) or ""):      # a title emptied to be typed again is not written
                    if self.write_title(node_id, new, lang, refresh_pane=False):
                        subject["titles"][lang] = new
                    else:
                        ok = False
        elif subject.get("has_title") and (state.title or "").strip() and state.title.strip() != (subject["title"] or "").strip():
            if self.write_title(node_id, state.title.strip(), refresh_pane=False):
                subject["title"] = state.title.strip()
            else:
                ok = False
        if bool(state.printed) != bool(subject["printed"]):
            if self.write_enabled(node_id, bool(state.printed), refresh_pane=False):
                subject["printed"] = bool(state.printed)
            else:
                ok = False
        return ok

    def write_heading_line(self, node_id, body):
        """A heading of a file with no tags edited in its pane: its title rewritten where it differs. Its level is not changed here -- tagging the file makes it an object, which has one."""
        subject = self.subject
        try:
            model = typst_objects.model_for_body("heading", body)
        except typst_objects.ModelError:
            return False
        if model.level != subject["level"]:
            return self.refuse("st_heading_level_fixed")
        if model.title == subject["title"]:
            return True
        if self.write_title(node_id, model.title, refresh_pane=False):
            subject["title"] = model.title
            return True
        return False

    def section_placement(self):
        """(parent id, position, words) for a new section or chapter: inside the chapter chosen, at its end; else right after the section chosen, under the same parent; else at the end of the document. The report has no chapters, so its place is among the include lines."""
        top = (None, None, self.t("st_where_top"))
        node = self.single()
        owner = node if node is not None and node.kind == "group" else self.file_node(node) if node is not None else None
        if owner is None:
            return top
        title = structure_tree.display_title(owner)
        if owner.kind == "group":
            return owner.id, None, self.t("st_where_inside", title=title)
        siblings = self.sibling_ids(owner.parent)
        if owner.id not in siblings:
            return top
        return (owner.parent or None), siblings.index(owner.id) + 1, self.t("st_where_after", title=title)

    def sibling_ids(self, parent_id):
        """The ids of the sections under `parent_id` (None for the top) in order -- the include lines of a report, the children of a chapter in structure.json."""
        here, mode = project.current(), self.mode()
        if mode == "rs":
            return [node.id for node in self.nodes if node.kind == "file"]
        try:
            source = structure.read(here.structure_file(mode))
        except (validation.ValidationError, OSError):
            return []
        if parent_id is None:
            return [entry["id"] for entry in source["sections"]]
        found = structure.find(source, parent_id)
        return [entry["id"] for entry in found[0].get("children", [])] if found is not None else []

    def on_add_section(self):
        if not self.writable():
            return
        parent, position, where = self.section_placement()
        answer = self.ask_section(where)
        if answer is not None:
            self.write_add_section(parent, position, *answer)

    def on_add_group(self):
        if not self.writable():
            return
        if self.mode() == "rs":
            self.refuse("st_why_rs_no_groups")
            return
        parent, position, where = self.section_placement()
        answer = self.ask_group(where)
        if answer is not None:
            self.write_add_group(parent, position, *answer)

    def write_add_section(self, parent, position, section_id, title):
        """A new section -- a file of its own -- added through structure.add_section and chosen."""
        self.failure = None
        try:
            edit = structure.add_section(project.current(), self.mode(), parent, position, section_id, title)
        except self.CAUGHT as exc:
            return self.fail(exc)
        self.update_banner()
        self.say(self.t("st_added", id=edit.id))
        self.reload(select=edit.id)
        self.tree.reveal(edit.id)
        return True

    def write_add_group(self, parent, position, group_id, titles):
        """A new, empty chapter added through structure.add_group and chosen."""
        self.failure = None
        try:
            edit = structure.add_group(project.current(), self.mode(), parent, position, group_id, titles)
        except self.CAUGHT as exc:
            return self.fail(exc)
        self.update_banner()
        self.say(self.t("st_group_added", id=edit.id))
        self.reload(select=edit.id)
        self.tree.reveal(edit.id)
        return True

    def on_remove(self):
        if not self.writable():
            return
        chosen = [node for node in self.selection() if node.kind in ("file", "group", "object")]
        if not chosen:
            self.say(self.t("st_off_none"))
            return
        # An object taken out stays in the tree, struck through, and comes back on the right button (the engineer's request of 06.10.2026): nothing to ask. A section or a chapter is still asked about.
        if all(node.kind == "object" for node in chosen):
            for node in reversed(chosen):
                if not self.remove_node(node):
                    break
            return
        if len(chosen) > 1:
            if self.ask_confirm(self.t("st_remove_ask_many", count=len(chosen))):
                for node in reversed(chosen):
                    if not self.remove_node(node):
                        break
            return
        node = chosen[0]
        title = structure_tree.display_title(node)
        folder = f"{self.doc_dir().name}/{structure.SECTIONS_DIR}/{structure.ARCHIVES_DIR}/"
        ask = self.t("st_remove_ask", title=title, folder=folder) if node.kind == "file" else self.t("st_remove_ask_group", title=title)
        if self.ask_confirm(ask):
            self.remove_node(node)

    def remove_node(self, node):
        if node.kind == "object":
            return self.write_remove_object(node.id)
        return self.write_remove(node.id)

    def write_remove(self, node_id):
        """Section or chapter `node_id` taken out of the document through structure.remove_section -- its file archived, never deleted. The row after it, or before it, or the chapter above is chosen next."""
        node = self.tree.node(node_id)
        if node is None:
            return False
        neighbour = self.neighbour_of(node)
        self.failure = None
        try:
            edit = structure.remove_section(project.current(), self.mode(), node_id)
        except self.CAUGHT as exc:
            return self.fail(exc)
        self.update_banner()
        self.say(self.t("st_removed", id=node_id, file=f"{structure.SECTIONS_DIR}/{structure.ARCHIVES_DIR}/{edit.archived[0].name}") if edit.archived else self.t("st_removed_empty", id=node_id))
        self.reload(select=neighbour, reset=not neighbour)
        return True

    def neighbour_of(self, node):
        """The id of the row to choose once `node` is gone: the next section at its level, else the one before, else the chapter it was in, else None."""
        siblings = self.sibling_ids(node.parent or None)
        if node.id in siblings:
            index = siblings.index(node.id)
            if index + 1 < len(siblings):
                return siblings[index + 1]
            if index > 0:
                return siblings[index - 1]
        return node.parent or None

    def on_rename(self):
        if not self.writable():
            return
        node = self.single()
        if node is None or node.kind not in ("file", "group"):
            self.say(self.t("st_off_none"))
            return
        new = self.ask_rename(node.id, structure_tree.display_title(node))
        if new and new != node.id:
            self.write_rename(node.id, new)

    def write_rename(self, node_id, new_id):
        """Section `node_id` given the id `new_id` through structure.rename_section -- its file renamed with it."""
        self.failure = None
        try:
            edit = structure.rename_section(project.current(), self.mode(), node_id, new_id)
        except self.CAUGHT as exc:
            return self.fail(exc)
        self.update_banner()
        self.say(self.t("st_renamed", old=node_id, id=edit.id))
        self.reload(select=edit.id)
        return True

    def write_move(self, node_id, parent, position):
        """Section or chapter `node_id` moved through structure.move_node -- under the chapter `parent` (None for the top) at `position` among its children. No file moves. True where it was moved or already stood there."""
        self.failure = None
        try:
            edit = structure.move_node(project.current(), self.mode(), node_id, parent, position)
        except self.CAUGHT as exc:
            return self.fail(exc, reload=False)
        self.update_banner()
        return True

    def ask_overwrite(self, found):
        """Whether the engineer lets an object written by hand be rewritten: told which of the two it is, and what will change -- the lines of the difference, or that what is written there cannot be read."""
        if found.state == "unreadable":
            lost = self.t("st_overwrite_unreadable")
        else:
            diff = found.diff()
            lost = self.t("st_overwrite_lost", diff=diff) if diff else "."
        return self.ask_confirm(self.t("st_overwrite_ask", id=found.id, lost=lost))

    def write_object(self, node_id, payload):
        """The body of object `node_id` written from what its pane holds -- `payload` is a model of the pane (written as its call), or a string for a heading and a paragraph -- and **nothing else of the file changes**. The body the pane was loaded with is what the write is checked against: where the object changed on disk since, nothing is written and the pane reads it again. An object written by hand asks first, once. Where the object stands in a block shared with another document, this document's copy alone is written and calc/sync.py told. True where it was written."""
        subject = self.subject
        node = self.tree.node(node_id)
        if node is None or subject is None or subject.get("id") != node_id or node.kind != "object":
            return False
        here, mode = project.current(), self.mode()
        path = self.doc_dir() / node.file
        self.failure = None
        try:
            text = typst_paths.read_text(path)
            found = typst_objects.find(text, node.object_id)
            if found is None:
                raise typst_objects.ObjectError("no_such_object", f"the file holds no object {node.object_id!r}", id=node.object_id)
            force = False
            if found.state != "canonical":
                if node_id not in self.forced:
                    if not self.ask_overwrite(found):
                        self.show_selection()       # what was typed is given up: the pane shows the file
                        return False
                    self.forced.add(node_id)
                force = True
            body = payload if isinstance(payload, str) else payload.to_call()
            new_text = typst_objects.write_object(text, node.object_id, body, force=force, expected=subject.get("body"))
            before = shared_block_text(text, found.shared) if found.shared else None
            if new_text != text:
                typst_paths.write_text(path, new_text)
        except typst_objects.ObjectError as exc:
            if exc.code == "changed":
                self.say(self.t("st_changed_outside"))
                self.failure = self.t("st_changed_outside")
                self.update_banner()
                self.show_selection()
                return False
            return self.fail(exc, reload=False)
        except self.CAUGHT as exc:
            return self.fail(exc, reload=False)
        again = typst_objects.find(new_text, node.object_id)
        subject["body"] = again.written if again is not None else subject.get("body")
        subject["state"] = again.state if again is not None else subject.get("state")
        self.update_banner()
        if before is not None and new_text != text:
            self.record_edit(found.shared, before)
        self.after_pane_write()
        return True

    def record_edit(self, shared_id, before):
        """calc/sync.py told that this document's copy of shared block `shared_id` was edited here: the other documents will see the edit as incoming. A record that cannot be written leaves the edit where it is -- written -- and says so."""
        try:
            sync.record_local_edit(project.current(), self.mode(), shared_id, before=before)
        except (sync.SyncError, OSError) as exc:
            self.failure = self.t("st_record_failed", error=self.why(exc))
            self.update_banner()

    def insert_place(self, node, text):
        """(line to insert after, the file node) for a new object where `node` is chosen: after the object's closing tag, or at the end of the file for a section or a heading. None where nothing is chosen that holds objects."""
        owner = self.file_node(node)
        if owner is None or node is None:
            return None
        if node.kind == "object" and node.span is not None:
            return node.span[1], owner
        return len(_lines(text)) - 1, owner

    def on_add_object(self):
        """The button itself: the menu of the kinds opens under it, which is what `setMenu` makes a click do."""
        return None

    def on_add_kind(self, kind, _checked=False):
        if self.writable():
            self.write_add_object(kind)

    def write_add_object(self, kind):
        """A new object of `kind` -- its type's defaults -- added after the object chosen, or at the end of the section chosen, **between blank lines**, and chosen. Refused where nothing chosen can hold it."""
        node = self.single()
        if node is None or node.kind == "group":
            return self.refuse("st_off_none")
        here, mode = project.current(), self.mode()
        owner = self.file_node(node)
        path = self.doc_dir() / owner.file
        self.failure = None
        try:
            text = typst_paths.read_text(path)
            line, owner = self.insert_place(node, text)
            object_id = typst_objects.suggest_id(text, kind)
            new_text = typst_objects.insert_object(text, line, kind, object_id)
            new_text = self.pad_blank(new_text, object_id)
            added = typst_objects.find(new_text, object_id)
            before = shared_block_text(text, added.shared) if added is not None and added.shared else None
            typst_paths.write_text(path, new_text)
        except self.CAUGHT as exc:
            return self.fail(exc, reload=False)
        self.update_banner()
        if before is not None:
            self.record_edit(added.shared, before)
        self.say(self.t("st_object_added", id=object_id, file=owner.file))
        new_id = f"{owner.id}/{object_id}"
        self.reload(select=new_id)
        self.tree.reveal(new_id)
        return True

    @staticmethod
    def pad_blank(text, object_id):
        """`text` with a blank line before and after the object `object_id` where it has none: Typst parts two paragraphs by a blank line, and a comment is none."""
        found = typst_objects.find(text, object_id)
        if found is None:
            return text
        lines = _lines(text)
        newline = typst_objects._newline_of(text)
        after = found.end + 1
        if after < len(lines) and lines[after].strip():
            lines.insert(after, newline)
        if found.start > 0 and lines[found.start - 1].strip():
            lines.insert(found.start, newline)
        return "".join(lines)

    def write_remove_object(self, node_id):
        """Object `node_id` taken out of its file -- **copied into the archives folder first**, as a section's file is moved there, so that nothing is lost -- and the neighbour chosen. An object in a shared block is an edit of that block, and calc/sync.py is told."""
        node = self.tree.node(node_id)
        if node is None or node.kind != "object":
            return False
        path = self.doc_dir() / node.file
        folder = self.doc_dir() / structure.SECTIONS_DIR / structure.ARCHIVES_DIR
        self.failure = None
        try:
            text = typst_paths.read_text(path)
            found = typst_objects.find(text, node.object_id)
            if found is None:
                raise typst_objects.ObjectError("no_such_object", f"the file holds no object {node.object_id!r}", id=node.object_id)
            block = "".join(_lines(text)[found.start:found.end + 1])
            after, before_id = removed_objects.neighbours(text, node.object_id)
            new_text = typst_objects.remove_object(text, node.object_id)
            new_text = self.close_blank(new_text, found.start)
            before = shared_block_text(text, found.shared) if found.shared else None
            archive = folder / f"{structure._stamp()}-{Path(node.file).stem}-{node.object_id}.typ"
            folder.mkdir(parents=True, exist_ok=True)
            typst_paths.write_text(archive, block)
            typst_paths.write_text(path, new_text)
            removed_objects.record(self.doc_dir(), node.file, found, archive, after, before_id)
        except self.CAUGHT as exc:
            return self.fail(exc, reload=False)
        self.update_banner()
        if before is not None:
            self.record_edit(found.shared, before)
        self.say(self.t("st_object_taken_out", title=structure_tree.display_title(node)))
        siblings = [child.id for child in (self.tree.node(node.parent).children if node.parent else []) if child.kind == "object"]
        index = siblings.index(node_id) if node_id in siblings else 0
        rest = [i for i in siblings if i != node_id]
        neighbour = (rest[index] if index < len(rest) else rest[-1]) if rest else node.parent
        self.reload(select=neighbour, reset=not neighbour)
        return True

    def write_restore(self, row_id):
        """The object a `removed` row stands for put back into its file (removed_objects.restore: right after the object that stood before it), chosen, and calc/sync.py told where it came back into a shared block. True where it was put back."""
        entry = getattr(self, "removed", {}).get(row_id)
        node = self.tree.node(row_id)
        if entry is None or node is None or not self.writable():
            return False
        self.failure = None
        try:
            path, new_text, object_id, old_text = removed_objects.restore(self.doc_dir(), entry)
        except (removed_objects.RemovedError, *self.CAUGHT) as exc:
            return self.fail(exc, reload=False)
        back = typst_objects.find(new_text, object_id)
        if back is not None and back.shared:
            self.record_edit(back.shared, shared_block_text(old_text, back.shared))
        self.update_banner()
        self.say(self.t("st_restored", title=structure_tree.display_title(node), file=entry["file"]))
        self.reload(select=f"{node.parent}/{object_id}")
        return True

    def write_forget_removed(self, row_id):
        """A `removed` row taken off the list: its entry out of the register, its copy left in the archives."""
        entry = getattr(self, "removed", {}).get(row_id)
        node = self.tree.node(row_id)
        if entry is None or node is None or not self.writable():
            return False
        try:
            removed_objects.forget(self.doc_dir(), entry)
        except OSError as exc:
            return self.fail(exc, reload=False)
        self.say(self.t("st_forgotten", title=structure_tree.display_title(node), archive=entry.get("archive", "")))
        self.reload(select=node.parent)
        return True

    @staticmethod
    def close_blank(text, line):
        """`text` after an object was cut out at `line`: one of the two blank lines that stood on either side of it taken out, so that a removal leaves one blank line where two objects meet and not two."""
        lines = _lines(text)
        if 0 < line < len(lines) and not lines[line].strip() and not lines[line - 1].strip():
            del lines[line]
        return "".join(lines)
