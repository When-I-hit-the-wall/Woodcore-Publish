"""The numbers of a load that may follow a variable of the export, written once (spec 2026-10-11-variables-liees-champs-et-textes, issue #42; spec 2026-10-23-onglets-types-et-services, ARCH-RISK-006).

A number of a load's form or table is wrapped in linkable_spin.LinkableSpin, whose button links it to a variable of another load or of a «Formule» domain -- the loads being computed first (links.LOADS, D-11) --; a link that would close a circle of loads is refused as it is chosen (REQ-007). `LinkSet` keeps the wrappers of one tab, puts a source's links into them and the wrappers' links into a draft. It is no service with a place on the screen: `LoadTab` holds one, and a tab built on a type offers one through its context (`ctx.links`), which its form and its table of layers use without knowing each other.
"""

import linkable_spin
import project
import registry
from domains import links


class LinkSet:
    """The linkable numbers of one tab. `app` is the window, `module` the domain (its `DOMAIN`, `LINKABLE`, `stamp_version`), `t` the window's words, `touch` what a link changed does, `draft()` the tab's draft and `case_id()` the id typed in its identity row -- both read when a link is chosen, never kept."""

    def __init__(self, app, module, t, touch, draft, case_id):
        self.app, self.module, self.t = app, module, t
        self.touch, self.draft, self.case_id = touch, draft, case_id
        self.linkables, self.wrappers = {}, {}
        self._values = None

    def linked(self, spin, key, unit, label, store=True):
        """`spin` with the button that links it to a variable; the widget the form or the table holds in its place. `store` False: a number whose link its owner keeps itself (a layer's, carried by its row)."""
        wrapper = linkable_spin.LinkableSpin(spin, unit, label, lambda: self.app, self.app.lang, links.LOADS, refuse=self.refuse)
        wrapper.changed.connect(self.touch)
        if store:
            self.linkables[key] = wrapper
            self.wrappers[id(spin)] = wrapper
        return wrapper

    def row_of(self, spin):
        """The widget a form row holds for `spin`: its wrapper where it may follow a variable -- what `setRowVisible` names."""
        return self.wrappers.get(id(spin), spin)

    def values(self):
        """The export's values, read once per filling of the form (`forget_values` before each)."""
        if self._values is None:
            self._values = linkable_spin.current_values()
        return self._values

    def forget_values(self):
        self._values = None

    def fill(self, s):
        found = links.links_of(s)
        for key, wrapper in self.linkables.items():
            wrapper.set_link(found.get(key), self.values() if found else {})

    def collect(self, s):
        """The wrappers' links into the draft `s` -- a layer's own carried by its row --, those of a field the draft does not hold taken off, and the schema_version that says whether any is left."""
        found = {key: w.link() for key, w in self.linkables.items() if w.link() is not None}
        if found:
            s[links.LINKS] = found
        else:
            s.pop(links.LINKS, None)
        links.drop_unheld(s, self.module.LINKABLE)
        self.module.stamp_version(s)

    def refuse(self, link):
        """A sentence where `link` would make this load follow, through others, a variable of its own (REQ-007), else None."""
        if link.get("origin") == links.FORMULAS:
            return None
        if not any(m.DOMAIN == self.module.DOMAIN for m in registry.DOMAIN_MODULES):
            return None   # no load (a member check, issue #112): nothing follows it, no circle can close through it
        node = (self.module.DOMAIN, (self.case_id() or "").strip())
        graph = registry.load_graph(project.current())
        draft = self.draft()
        graph[node] = registry.load_targets(draft, self.module.DOMAIN) | {(link["domain"], link["instance"])}
        chain = links.find_cycle(graph, node)
        if chain:
            return self.t("ld_link_circle", chain=" → ".join("%s/%s" % pair for pair in chain))
        return None
