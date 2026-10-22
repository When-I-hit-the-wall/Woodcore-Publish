"""StructureTab's view -- the files it watches, the tree, the selection, the right pane and the page compiled beside it -- a mixin of methods moved verbatim out of calc/tools/structure_tab.py (issue #30). StructureTab names it among its bases.
"""

import functools
from pathlib import Path
import shiboken6
from PySide6.QtCore import QFileSystemWatcher, QTimer, Qt
import doc_import  # what is imported from another document, and an object's move (calc/doc_import.py)
import documents  # what each of the three documents is called (calc/documents.py)
import object_panes  # the right pane (calc/tools/object_panes.py)
import project
import removed_objects  # the objects taken out of the document, kept where they stood (calc/removed_objects.py)
import structure  # the tree, and everything that writes the structure (calc/structure.py)
import structure_preview  # the Typst source of what is chosen (calc/structure_preview.py)
import structure_tree  # the tree widget (structure_tree.py)
import structure_words  # the words (structure_words.py)
import typst_objects  # the objects of a file, and the writing of one (calc/typst_objects.py)
import typst_paths
import validation


STRINGS = structure_words.STRINGS


class StructureTabViewMixin:
    """Methods of structure_tab.StructureTab, moved verbatim (issue #30): the class names this mixin among its bases."""

    def watched_files(self):
        """The files whose change the tree must be read again for: the document's entry file, its structure.json and every section of its `Sections/` folder -- the archives folder left out."""
        here, mode = project.current(), self.mode()
        files = [Path(here.document_typ(mode))]
        structure_file = here.structure_file(mode)
        if structure_file is not None:
            files.append(Path(structure_file))
        sections = self.doc_dir() / structure.SECTIONS_DIR
        if sections.is_dir():
            files += sorted(path for path in sections.glob("*.typ") if path.is_file())
        return files

    def disk_signature(self):
        """What the files say now: each one's name, size and the time it was written. A change by any editor, VS Code or this tab, is a signature that differs."""
        out = []
        for path in self.watched_files():
            try:
                found = path.stat()
            except OSError:
                continue
            out.append((path.name, found.st_size, found.st_mtime_ns))
        return tuple(out)

    def start_watching(self):
        """The document's folder and files watched, from now until the tab is hidden. Made when the tab is shown and not before: a watch holds the directory on Windows, so a tab nobody looks at holds nothing."""
        if self.watcher is None:
            self.watcher = QFileSystemWatcher(self)
            self.watcher.fileChanged.connect(self.on_files_changed)
            self.watcher.directoryChanged.connect(self.on_files_changed)
        self.watch_paths()

    def watch_paths(self):
        """Every path the watcher should hold held: a file replaced by an editor's atomic save drops out of it, so this is made again after every change."""
        if self.watcher is None:
            return
        wanted = [str(path) for path in self.watched_files()]
        sections = self.doc_dir() / structure.SECTIONS_DIR
        if sections.is_dir():
            wanted.append(str(sections))
        have = set(self.watcher.files()) | set(self.watcher.directories())
        missing = [path for path in wanted if path not in have]
        if missing:
            self.watcher.addPaths(missing)

    def stop_watching(self):
        """Nothing watched: the directories are let go of."""
        if self.watcher is not None:
            held = self.watcher.files() + self.watcher.directories()
            if held:
                self.watcher.removePaths(held)
        self.external_timer.stop()

    def on_files_changed(self, _path=""):
        """A file or the folder changed: the tree is read again a moment from now, if what is on disk is not what was read last."""
        if shiboken6.isValid(self):
            self.external_timer.start()

    def reload_external(self, quiet=False):
        """The tree read again -- the pane of the object chosen with it -- where the files are not what they were when it was last read. True where it was. The files this tab wrote itself are what it read last, so they are not read again; what a pane has pending is written first, and refused if the file changed under it."""
        if not shiboken6.isValid(self):
            return False
        self.watch_paths()
        signature = self.disk_signature()
        if signature == self.signature:
            return False
        self.host.flush()
        self.reload()
        if not quiet:
            self.say(self.t("st_reloaded"))
        return True

    def reload(self, select=None, reset=False, state=None, pane=True):
        """The structure read afresh and the tree filled again with what it says -- the rows open still open, the rows chosen still chosen (`select` names an id or ids to choose instead, `reset` none, `state` the state of the tree to give back where it is not the tree's own: what a rebuilt window carries). With `pane`, what the right pane and the page show is made again for the rows chosen. A structure that cannot be read is said in the banner and lists nothing.

        Where this is asked from inside one of the tree's own signals -- an edit pending in a pane written because another row was chosen -- the tree is not cleared there, which crashes: it is read again a moment later."""
        if self._in_tree_signal:
            QTimer.singleShot(0, functools.partial(self.deferred, functools.partial(self.reload, select, reset, state, pane)))
            return
        if state is None:
            state = None if reset else self.tree.state()
        if select:
            ids = [select] if isinstance(select, str) else list(select)
            state = dict(state or {}, selection=ids, selected=ids[0] if ids else "")
        try:
            self.nodes = structure.tree(project.current(), self.mode())
            self.error = None
        except (validation.ValidationError, project.ProjectError, OSError) as exc:     # a StructureError is a ValidationError
            self.nodes, self.error = [], str(exc)
        self.add_removed()
        self.signature = self.disk_signature()
        self.tree.set_nodes(self.nodes, tips=self.tips, state=state, sync=self.sync_state, sync_tips=self.sync_tip, typ_mark=self.mode() == "rs",
                            stopped=self.stopped_ids(), stopped_tip=self.t("st_tip_stopped"),
                            whole_label=self.t("st_whole_document"), whole_tip=self.t("st_whole_tip"))
        self.update_banner()
        self.update_buttons()
        self.watch_paths()
        if pane:
            self.show_selection()
        self.sync_timer.start()

    def deferred(self, slot):
        if shiboken6.isValid(self):
            slot()

    def add_removed(self):
        """The objects taken out of the document (calc/removed_objects.py) added to the tree as rows of kind `removed`, each among its file's objects at the place it stood: right after the object that stood before it, else right before the one that stood after it, else at the end. Their entries are kept by row id (`self.removed`), for the right button."""
        self.removed = {}
        doc_dir = self.doc_dir()
        if doc_dir is None:
            return
        entries = removed_objects.read(doc_dir)
        if not entries:
            return
        for node in structure.flatten(self.nodes):
            if node.kind != "file" or not node.file:
                continue
            mine = [entry for entry in entries if entry["file"] == node.file]
            for index, entry in enumerate(mine):
                ids = [child.object_id for child in node.children]
                if entry.get("after") in ids:
                    at = ids.index(entry["after"]) + 1
                elif entry.get("before") in ids:
                    at = ids.index(entry["before"])
                else:
                    at = len(node.children)
                previous = node.children[at - 1] if at > 0 else None
                level = previous.level if previous is not None and previous.level is not None else (node.level or 1) + 1
                row_id = f"{node.id}/~removed-{index}-{entry['object_id']}"
                node.children.insert(at, structure.Node("removed", row_id, entry.get("title") or entry["object_id"], level, file=node.file, enabled=False, active=False,
                                                        parent=node.id, object_type=entry.get("type"), object_id=entry["object_id"]))
                self.removed[row_id] = entry

    def stopped_ids(self):
        """The files of the document shown whose sharing was stopped while the tab was open, by node id."""
        return self.stopped.setdefault(self.mode(), set())

    def update_banner(self):
        text = self.t("st_banner_unreadable", error=self.error) if self.error else (self.failure or "")
        self.banner.setText(text)
        self.banner.setVisible(bool(text))
        if getattr(self, "levels_box", None) is not None:
            self.levels_box.setVisible(self.relative_levels())

    def relative_levels(self):
        """Whether the document shown is a convention or a base laid out with offsets -- its headings written as `=` whatever their depth, its chapters' titles in its entry -- which the banner offers to convert."""
        mode = self.mode()
        if mode not in structure.MODES or self.error:
            return False
        try:
            path = project.current().structure_file(mode)
            return path is not None and path.is_file() and not structure.is_absolute(structure.read(path))
        except (validation.ValidationError, project.ProjectError, OSError):
            return False

    def on_make_absolute(self):
        """«Écrire les titres à leur niveau réel»: the convention and the base converted together (structure.make_absolute) once the engineer agrees, and the tree read again."""
        if not self.writable() or not self.ask_confirm(self.t("st_levels_ask")):
            return False
        self.failure = None
        try:
            written = structure.make_absolute(project.current())
        except self.CAUGHT as exc:
            return self.fail(exc)
        self.say(self.t("st_levels_done", count=len(written)))
        self.reload()
        return True

    def expand_to(self, level, _checked=False):
        self.tree.expand_to(level)

    def kind_name(self, kind):
        key = "st_kind_" + str(kind)
        return self.t(key) if key in STRINGS["en"] else str(kind)

    def tips(self, node):
        """The three tooltips of a row: its title's (where it is stored, why it is not printed, what is wrong with it), the `.typ` mark's and the link mark's."""
        lines = []
        if node.kind == "removed":
            entry = getattr(self, "removed", {}).get(node.id, {})
            return self.t("st_tip_removed", date=str(entry.get("removed", "")).replace("T", " ")), "", ""
        if node.kind == "object" and node.span is not None:
            lines.append(self.t("st_tip_object", type=self.kind_name(node.object_type), first=node.span[0] + 1, last=node.span[1] + 1, file=node.file))
            if node.state == "hand_edited":
                lines.append(self.t("st_tip_hand"))
            elif node.state == "unreadable":
                lines.append(self.t("st_tip_unreadable"))
        elif node.file:
            lines.append(f"{node.file}:{node.line + 1}" if node.kind == "heading" and node.line is not None else node.file)
        if not node.active:
            lines.append(self.t("st_tip_off" if not node.enabled else "st_tip_parent_off"))
        lines += [self.t("st_tip_problem", problem=problem) for problem in node.problems]
        typ = self.t("st_tip_typ", file=node.file) if node.separate_file and node.file else ""
        lang = getattr(self.app, "lang", documents.DEFAULT_LANGUAGE)
        shared = self.t("st_tip_shared", documents=", ".join(documents.mode_name(mode, lang) for mode in node.shared_with)) if node.shared_with else ""
        return "\n".join(lines), typ, shared

    def file_node(self, node):
        """The file node a node of the tree stands in -- itself where it is one; None for a chapter."""
        while node is not None and node.kind != "file":
            node = self.tree.node(node.parent) if node.parent else None
        return node

    def selection(self):
        """The nodes chosen, in document order."""
        return [self.tree.node(node_id) for node_id in self.tree.selected_ids() if self.tree.node(node_id) is not None]

    def single(self):
        """The one node chosen, None where none is or several are."""
        chosen = self.selection()
        return chosen[0] if len(chosen) == 1 else None

    def on_selection_changed(self, _ids=None):
        """The rows chosen changed by the user's hand: what a pane had pending is written first -- before anything it would be written to changes --, then the right pane and the page show what is chosen now."""
        self._in_tree_signal = True
        try:
            self.host.flush()
            self.show_selection()
        finally:
            self._in_tree_signal = False

    def show_selection(self):
        """The right pane, the buttons and the page made for the rows chosen: none shows a sentence and the whole document, one its pane and its page, several a sentence and their pages one after the other."""
        chosen = self.selection()
        self.update_buttons()
        if len(chosen) == 1 and chosen[0].kind == "removed":
            entry = getattr(self, "removed", {}).get(chosen[0].id, {})
            self.subject = None
            self.host.show_text(self.t("st_removed_note", title=structure_tree.display_title(chosen[0]), archive=entry.get("archive", "")))
        elif not chosen:
            self.subject = None
            self.host.clear()
        elif len(chosen) > 1:
            self.subject = None
            self.host.show_many(len(chosen))
        else:
            self.load_pane_for(chosen[0])
        self.request_preview()

    def group_titles(self, group_id):
        path = project.current().structure_file(self.mode())
        if path is None:
            return {}
        try:
            found = structure.find(structure.read(path), group_id)
        except (validation.ValidationError, OSError):
            return {}
        return dict(found[0].get("title") or {}) if found is not None else {}

    def read_text(self, node):
        """The text of the section file a node stands in, None where it cannot be read."""
        owner = self.file_node(node)
        if owner is None or not owner.file:
            return None
        try:
            return typst_paths.read_text(self.doc_dir() / owner.file)
        except (OSError, UnicodeDecodeError):
            return None

    @staticmethod
    def has_untagged(text):
        """Whether a file's text holds a heading or a paragraph no object tag wraps -- what «Baliser ce fichier» tags; False where its tags cannot be read."""
        if text is None:
            return False
        try:
            return bool(typst_objects.untagged(text))
        except typst_objects.ObjectError:
            return False

    def load_pane_for(self, node):
        """The right pane shown over `node`: a chapter's or a section's state, an object's pane by its kind, a heading of an untagged file as a heading. What is loaded is remembered as `subject` -- the one place an edit of the pane is written to."""
        self.forced = {key for key in self.forced if key == node.id}
        self.loading = True
        try:
            if node.kind == "group":
                state = object_panes.NodeState(id=node.id, title=structure_tree.display_title(node), titles=self.group_titles(node.id), printed=bool(node.enabled), untagged=False, has_title=True)
                self.subject = {"id": node.id, "kind": "chapter", "titles": dict(state.titles), "printed": state.printed}
                self.host.show_object("chapter", state, self.context)
            elif node.kind == "file":
                text = self.read_text(node)
                state = self.section_state(node, text)
                self.subject = {"id": node.id, "kind": "section", "title": state.title, "printed": state.printed, "has_title": state.has_title}
                self.host.show_object("section", state, self.context)
            elif node.kind == "object":
                text = self.read_text(node)
                found = typst_objects.find(text, node.object_id) if text is not None else None
                if found is None:
                    self.subject = None
                    self.host.clear()
                    return
                self.subject = {"id": node.id, "kind": found.type, "object": found.id, "file": node.file, "body": found.written, "state": found.state, "shared": found.shared}
                self.host.show_object(found.type, found, self.context)
            else:
                text = self.read_text(node)
                heading = None
                if text is not None:
                    heading = next((h for h in structure.scan_headings(text) if h.line == node.line), None)
                if heading is None:
                    self.subject = None
                    self.host.clear()
                    return
                body = "=" * heading.level + " " + heading.title
                self.subject = {"id": node.id, "kind": "heading-line", "level": heading.level, "title": heading.title}
                self.host.show_object("heading", body, self.context)
        finally:
            self.loading = False

    def section_title_editable(self, node, text):
        """Whether the title of the file `node` can be set here: the file has a first heading -- an object of it where the file is tagged, which is the same line -- whose title is plain text Woodcore can rewrite (`structure.set_title`)."""
        if text is None or node.line is None:
            return False
        heading = next((found for found in structure.scan_headings(text) if found.line == node.line), None)
        return heading is not None and heading.span is not None

    def section_state(self, node, text):
        """What the right pane shows of a section: its title (the first heading of its file, tagged or not), its file, whether it is printed, which documents it is shared with and whether it can be shared at all -- the project having another document."""
        here, mode = project.current(), self.mode()
        lang = getattr(self.app, "lang", documents.DEFAULT_LANGUAGE)
        try:
            others = doc_import.other_documents(here, mode)
        except (validation.ValidationError, project.ProjectError):
            others = ()
        has_title = self.section_title_editable(node, text)
        return object_panes.NodeState(
            id=node.id, title=structure.plain_title(node.title or "") if has_title else "", printed=bool(node.enabled), untagged=self.has_untagged(text),
            has_title=has_title, file=node.file or "", shared_with=tuple(documents.mode_name(mode_, lang) for mode_ in node.shared_with), sharing=bool(others))

    def on_pane_changed(self, kind, payload):
        """What a pane changed, written to where it came from: a section's or a chapter's state through calc/structure.py, an object's body between its tags."""
        subject = self.subject
        if subject is None or self.loading:
            return
        if kind == "chapter" and subject["kind"] == "chapter":
            self.write_node_state(subject["id"], payload)
        elif kind == "section" and subject["kind"] == "section":
            self.write_node_state(subject["id"], payload)
        elif subject["kind"] == "heading-line":
            self.write_heading_line(subject["id"], payload)
        elif kind == subject["kind"]:
            self.write_object(subject["id"], payload)

    def after_pane_write(self):
        """The tree's rows brought up to date after a pane wrote -- in place, where the nodes are the same, so that the pane and the selection stay as they are -- and the page asked for."""
        try:
            nodes = structure.tree(project.current(), self.mode())
        except (validation.ValidationError, project.ProjectError, OSError):
            nodes = None
        if nodes is not None and self.tree.update_nodes(nodes, self.tips):
            self.nodes = nodes
            self.signature = self.disk_signature()
            self.update_buttons()
        else:
            QTimer.singleShot(0, self.deferred_reload)
        self.sync_timer.start()
        self.request_preview()

    def deferred_reload(self):
        if shiboken6.isValid(self):
            self.reload(pane=False)

    def load_pane(self, auto=False):
        """The page shown the document of the window -- its preview, its own PDF, or nothing yet. With `auto`, and only where nothing is chosen and there is nothing to show, a compile of the document is asked for as well: a project that has never been compiled is the only one whose page would be empty for good. Where something is chosen, its snippet is asked for."""
        here, mode = project.current(), self.mode()
        self.pane_loaded = True
        self.form_seen = self.form_signature()
        if not here.is_created(mode):   # a document not made yet (issue #90): nothing to show, nothing to compile
            self.pane.clear()
            return
        try:
            self.pane.set_document(here, mode)
        except project.ProjectError:
            self.pane.clear()
            return
        if self.tree.selected_ids():
            self.request_preview()
        elif self.resume:
            self.resume = False
            if not self.read_only():
                self.pane.request(here, mode)
        elif auto and not self.read_only() and not self.pane.showing and not self.pane.is_pending():
            self.pane.request(here, mode)

    def preview_words(self, ids):
        """What the page is the preview of, in words: the document, a node, a number of them."""
        if not ids:
            return self.t("st_preview_document")
        if len(ids) > 1:
            return self.t("st_preview_many", count=len(ids))
        node = self.tree.node(ids[0])
        what = self.t("st_preview_node", title=structure_tree.display_title(node)) if node is not None else ""
        return self.t("st_preview_not_printed", what=what) if node is not None and not node.active else what

    def request_preview(self, force=False):
        """The page asked to show what is chosen: its snippet where something is, the whole document where nothing is. Not before the page has been given its document -- the tab shown --, and not where the structure cannot be read."""
        ids = [node_id for node_id in self.tree.selected_ids() if node_id not in getattr(self, "removed", {})]    # an object taken out has no page
        self.preview_label.setText(self.t("st_preview", what=self.preview_words(ids)))
        if not self.pane_loaded or self.error:
            return None
        here, mode = project.current(), self.mode()
        if not here.is_created(mode):
            return None
        snippet = None
        if ids:
            try:
                snippet = structure_preview.build(here, mode, self.nodes, ids)
            except (validation.ValidationError, OSError) as exc:
                self.failure = self.why(exc)
                self.update_banner()
        if snippet is None:
            self.pane.show_document()
            if force and not self.read_only():
                self.pane.request(here, mode)
            elif not self.pane.showing and not self.read_only() and not self.pane.is_pending():
                self.pane.request(here, mode)
            return None
        self.pane.request_snippet(here, mode, snippet.source, snippet.key)
        return snippet


    def compile_now(self, _checked=False):
        """The button: the whole document compiled at once, in the background -- the page showing it where nothing is chosen."""
        if self.read_only():
            return
        self.pane_loaded = True
        self.pane.request(project.current(), self.mode())
        self.pane.compile_now()

    def on_failed(self, _mode, _message):
        """A compile that failed: Typst's own message is in the pane's banner -- the status line only points at it."""
        self.say(self.t("st_compile_failed"))

    def on_stale_changed(self, stale):
        """The document's preview is not what its sources would give, and nothing is chosen: it is compiled again. A snippet is never stale."""
        if stale and self.pane_loaded and not self.read_only() and not self.tree.selected_ids() and not self.pane.is_pending():
            self.pane.request(project.current(), self.mode())
