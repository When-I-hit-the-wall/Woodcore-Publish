"""The «Dépendances» tab: the graph of the project's objects, read off data/dependencies.json (spec docs/requirements/completed/2026-10-21-graphe-dependances.md, UI-001, D-05; calc/domains/dependency_graph.py, docs/ui/tab-dependencies.md).

A browser, like «Variables»: it writes nothing and has no `dirty` (data_tab.py says why), so it defines no method `tab_guard.WRITERS` names. Since issue #106 the tab is a class of parameters on the type «Données» (data_tab.DataTab): the banner is the type's (`ExportBanner`, told through the context), the rest one whole service, `DependenciesBrowser`, found by `tab.service("browser")`. On the left, the objects of the last export by kind -- positions, loads, scripts, domains, checks… --, a filter above them; on the right, for the one chosen, **what it depends on** and **what depends on it** -- downstream transitively, the way the export's warnings count it --, each line naming the field or the command it is read through. A double click opens the object in its own tab (`MainWindow.open_object`), a section in the editor at the line of its call. A banner says when the graph is older than one of its objects' sources: the next export draws it again. The graph is read again each time the tab is shown; nothing is computed here.

The tab's words, `dg_`, in the window's three languages, are merged into woodcore_gui's STRINGS; the kinds are said with the export's own words (`warn_dep_kind_<kind>`). It must not import woodcore_gui, which imports it.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

import project
from data_tab import DataTab
from domains import dependency_graph as graph_model
from tab_frame import Service

KEY = "tab_dependencies"

STRINGS = {
    "fr": {
        "tab_dependencies": "Dépendances",
        "dg_filter": "Filtrer les objets…",
        "dg_objects": "Objets",
        "dg_depends_on": "Dépend de",
        "dg_used_by": "Utilisé par",
        "dg_none": "—",
        "dg_not_exported": "Le graphe n’a pas encore été écrit : lancez « Importer les données » (un export) pour le construire.",
        "dg_stale": "Le graphe date d’avant la dernière modification de {files} : le prochain export le refait.",
        "dg_unresolved": "{count} appel(s) de cette section nomment un objet que Woodcore ne situe pas (un registre propre au document).",
        "dg_all": "tous ({kind})",
        "dg_no_tab": "{node} n’a pas d’onglet où l’ouvrir (un cas lu dans le classeur, par exemple).",
        "dg_hint": "Double-cliquez sur un objet pour l’ouvrir dans son onglet.",
    },
    "de": {
        "tab_dependencies": "Abhängigkeiten",
        "dg_filter": "Objekte filtern…",
        "dg_objects": "Objekte",
        "dg_depends_on": "Hängt ab von",
        "dg_used_by": "Verwendet von",
        "dg_none": "—",
        "dg_not_exported": "Der Graph ist noch nicht geschrieben: «Daten importieren» (ein Export) baut ihn.",
        "dg_stale": "Der Graph ist älter als die letzte Änderung von {files}: der nächste Export baut ihn neu.",
        "dg_unresolved": "{count} Aufruf(e) dieses Abschnitts nennen ein Objekt, das Woodcore nicht zuordnet (ein Register des Dokuments selbst).",
        "dg_all": "alle ({kind})",
        "dg_no_tab": "{node} hat keinen Reiter, in dem es sich öffnen lässt (etwa ein Fall aus der Arbeitsmappe).",
        "dg_hint": "Doppelklick öffnet ein Objekt in seinem Reiter.",
    },
    "en": {
        "tab_dependencies": "Dependencies",
        "dg_filter": "Filter the objects…",
        "dg_objects": "Objects",
        "dg_depends_on": "Depends on",
        "dg_used_by": "Used by",
        "dg_none": "—",
        "dg_not_exported": "The graph is not written yet: run «Import data» (an export) to build it.",
        "dg_stale": "The graph is older than the last change of {files}: the next export draws it again.",
        "dg_unresolved": "{count} call(s) of this section name an object Woodcore cannot place (a document's own registry).",
        "dg_all": "all ({kind})",
        "dg_no_tab": "{node} has no tab to open it in (a case read from the workbook, for one).",
        "dg_hint": "Double-click an object to open it in its tab.",
    },
}

_NODE = Qt.ItemDataRole.UserRole


class DependenciesBrowser(Service):
    """The graph of the last export: the objects by kind on the left, what the one chosen depends on and what depends on it on the right -- the tab's one whole service (D-03 of the spec 2026-10-24-type-donnees). It reads, never writes."""

    NAME = "browser"
    ZONE = "body"
    NEEDS = ("read", "newer_sources", "upstream", "downstream")

    def mount(self, ctx):
        super().mount(ctx)
        self.t = ctx.t
        self.graph = None
        self.widget = QWidget()
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(6, 6, 6, 6)
        self.filter = QLineEdit()
        self.filter.setPlaceholderText(self.t("dg_filter"))
        self.filter.textChanged.connect(self.fill_objects)
        layout.addWidget(self.filter)
        self.splitter = splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)   # a pane dragged to nothing would have no arrow to come back by (chrome.FoldablePane)
        self.objects = QTreeWidget()
        self.objects.setHeaderLabels([self.t("dg_objects")])
        self.objects.currentItemChanged.connect(self.on_object)
        self.objects.itemDoubleClicked.connect(lambda item, _col: self.open(item.data(0, _NODE)))
        splitter.addWidget(self.objects)
        right = QWidget()
        column = QVBoxLayout(right)
        column.setContentsMargins(0, 0, 0, 0)
        self.note = QLabel("")
        self.note.setWordWrap(True)
        column.addWidget(self.note)
        row = QHBoxLayout()
        self.depends_on, self.used_by = QListWidget(), QListWidget()
        for title, widget in (("dg_depends_on", self.depends_on), ("dg_used_by", self.used_by)):
            box = QVBoxLayout()
            box.addWidget(QLabel("<b>%s</b>" % self.t(title)))
            box.addWidget(widget, 1)
            widget.itemDoubleClicked.connect(lambda item: self.open(item.data(_NODE)))
            row.addLayout(box, 1)
        column.addLayout(row, 1)
        hint = QLabel(self.t("dg_hint"))
        hint.setWordWrap(True)
        column.addWidget(hint)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, 1)
        self.reload()
        return self.widget

    # -- surviving a rebuild of the window: the filter and the object chosen (the splitter's sizes are the frame's) --

    def state(self):
        """What the tab keeps through a rebuilt window (woodcore_gui.rebuild, refresh_tab): its filter, the object chosen."""
        return {"filter": self.filter.text(), "node": self.current_node()}

    def restore(self, state):
        if state.get("filter"):
            self.filter.setText(state["filter"])
        if state.get("node"):
            self.select(state["node"])

    # -- reading ---------------------------------------------------------------------

    def shown(self):
        """The graph read again each time the tab is shown: an export may have drawn it since."""
        self.reload()

    def reload(self):
        """The graph read off data/dependencies.json, the banner told whether it is missing or older than one of its objects' sources, the lists filled."""
        here = project.current()
        self.graph = graph_model.read(here.data_dir / graph_model.EXPORT_FILE)
        if self.graph is None:
            self.ctx.say(self.t("dg_not_exported"))
        else:
            newer = graph_model.newer_sources(here, self.graph)
            self.ctx.say(self.t("dg_stale", files=", ".join(newer[:3]) + (" …" if len(newer) > 3 else "")) if newer else "")
        self.up = graph_model.upstream(self.graph) if self.graph else {}
        self.down = graph_model.downstream(self.graph) if self.graph else {}
        self.fill_objects()

    def kind_word(self, kind):
        return self.t("warn_dep_kind_" + kind)

    def fill_objects(self, *_args):
        chosen = self.current_node()
        self.objects.clear()
        needle = self.filter.text().strip().lower()
        for kind in graph_model.KINDS:
            nodes = [n for n in (self.graph or {}).get("nodes", {}) if graph_model.kind_of(n) == kind and needle in n.split(":", 1)[1].lower()]
            if not nodes:
                continue
            group = QTreeWidgetItem([f"{self.kind_word(kind)} ({len(nodes)})"])
            group.setFlags(group.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.objects.addTopLevelItem(group)
            for node in nodes:
                item = QTreeWidgetItem([node.split(":", 1)[1]])
                item.setData(0, _NODE, node)
                group.addChild(item)
                if node == chosen:
                    self.objects.setCurrentItem(item)
            group.setExpanded(bool(needle) or len(nodes) <= 12)
        if self.current_node() is None:
            self.show_node(None)

    def current_node(self):
        item = self.objects.currentItem()
        return item.data(0, _NODE) if item is not None else None

    def select(self, node):
        """Chooses `node` in the list: what a test, or another tab, asks for."""
        for i in range(self.objects.topLevelItemCount()):
            group = self.objects.topLevelItem(i)
            for j in range(group.childCount()):
                if group.child(j).data(0, _NODE) == node:
                    self.objects.setCurrentItem(group.child(j))
                    return True
        return False

    def on_object(self, current, _previous):
        self.show_node(current.data(0, _NODE) if current is not None else None)

    def lines(self, node, direction):
        """The lines of one side for `node`: (text, node) -- upstream the edges it reads, each with its field; downstream every object that depends on it, transitively."""
        if direction == "up":
            out = []
            for edge in self.graph["edges"]:
                if edge["from"] != node:
                    continue
                to = edge["to"]
                kind, ident = to.split(":", 1)
                name = self.t("dg_all", kind=self.kind_word(kind)) if ident == "*" else f"{self.kind_word(kind)} · {ident}"
                detail = edge.get("variable") or edge["field"]
                out.append((f"{name}  ({detail}{', l. %d' % edge['line'] if edge.get('line') else ''})", None if ident == "*" else to))
            return out
        return [(f"{self.kind_word(graph_model.kind_of(n))} · {n.split(':', 1)[1]}", n) for n in graph_model.reachable(self.down, node)]

    def show_node(self, node):
        for widget in (self.depends_on, self.used_by):
            widget.clear()
        self.note.setText("")
        if node is None or self.graph is None:
            return
        for widget, direction in ((self.depends_on, "up"), (self.used_by, "down")):
            found = self.lines(node, direction)
            for text, target in found or [(self.t("dg_none"), None)]:
                item = QListWidgetItem(text)
                item.setData(_NODE, target)
                widget.addItem(item)
        unresolved = self.graph["nodes"].get(node, {}).get("unresolved")
        if unresolved:
            self.note.setText(self.t("dg_unresolved", count=unresolved))

    # -- opening -----------------------------------------------------------------------

    def open(self, node):
        """The object opened where it is edited: a section in the editor at its first call, any other in its tab (`MainWindow.open_object`)."""
        if not node:
            return False
        opener = getattr(self.app, "open_object", None)
        if opener is not None and opener(node, (self.graph or {}).get("nodes", {}).get(node, {}).get("file")):
            return True
        if hasattr(self.app, "set_status"):
            self.app.set_status(self.t("dg_no_tab", node=node))
        return False


class DependenciesTab(DataTab):
    """The tab: the type's banner, and the browser of the graph. Parameters only (tests/test_tab_overrides.py)."""

    KEY = KEY
    MODULE = graph_model
    SERVICES = DataTab.SERVICES + (DependenciesBrowser,)
