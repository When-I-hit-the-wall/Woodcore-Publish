"""The list of a member check tab, a service (spec docs/requirements/completed/2026-10-24-verifications-elements-v3.md, UI-003; issue #112).

The type's list (case_list.CaseList) -- «Archives», «Nouveau» · «Dupliquer» · «Supprimer», the dot of unsaved changes -- with the checks **grouped by position** («T001 · Poutre», «Sans position») and **each its utilisation in percent**, green at 100 % or less, red above, no orange; a check that cannot be calculated shows «—» and says why in its tooltip. Two buttons sort it: **by position** (the groups, the ids in order) or **by rate** (one list, the highest first, the checks without one last). The order is the rule's, never a kept one (`KEEPS_ORDER`), and a drop files nothing into a folder: the position is the check's to say, in its head «Élément».

What a check's row says is the domain's (`list_rows`: the position, its label, the utilisation computed as the tab computes it, read off the last export); the words are the tab's (`vc_list_`), the colours the theme's.
"""

from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget

import grouped_list
import project
import theme
from case_list import CaseList
from check_rows import decimal

SORTS = ("position", "rate")


class CheckList(CaseList):
    """The list of the checks grouped by position, with their rates -- see the module's docstring."""

    KEEPS_ORDER = False
    NEEDS = ("list_rows",)

    def mount(self, ctx):
        self.sort = "position"
        self.rows = {}
        box = super().mount(ctx)
        line = QWidget()
        row = QHBoxLayout(line)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        self.sort_group = QButtonGroup(line)
        self.sort_group.setExclusive(True)
        self.sort_buttons = {}
        for key in SORTS:
            button = QPushButton(self.t("vc_list_sort_" + key))
            button.setCheckable(True)
            button.setProperty("choice", True)
            button.setChecked(key == self.sort)
            button.clicked.connect(lambda _c=False, k=key: self.set_sort(k))
            self.sort_group.addButton(button)
            self.sort_buttons[key] = button
            row.addWidget(button)
        row.addStretch(1)
        box.layout().insertWidget(1, line)
        return box

    def set_sort(self, key):
        """The list sorted by position or by rate, the case open kept chosen."""
        self.sort = key if key in SORTS else "position"
        for k, button in self.sort_buttons.items():
            button.setChecked(k == self.sort)
        self.reload_list(self.current_id)

    # --- what the list shows -----------------------------------------------------------

    def _group(self, label):
        return (label or self.t("vc_list_no_position")) if self.sort == "position" else grouped_list.ROOT_GROUP

    def listed(self):
        """The saved checks, `(id, text, group)`: «DR-01   76,0 %» under its position, or all in one list by rate."""
        ids = list(self.ctx.store.ids())
        try:
            here = project.current()
            self.rows = self.ctx.module.list_rows(here, ids)
        except project.ProjectError:
            self.rows = {}
        lang = self.app.lang
        out = []
        for cid in ids:
            said = self.rows.get(cid) or {}
            eta = said.get("eta")
            rate = (decimal(round(eta * 100, 1), lang, 1) + " %") if eta is not None else "—"
            out.append((cid, "%s   %s" % (cid, rate), self._group(said.get("position_label"))))
        if self.sort == "rate":
            out.sort(key=lambda r: (self.rows.get(r[0], {}).get("eta") is None, -(self.rows.get(r[0], {}).get("eta") or 0), r[0]))
        else:
            out.sort(key=lambda r: (r[2] == self.t("vc_list_no_position"), r[2].lower(), r[0]))
        return out

    def draft_group(self):
        pid = (self.ctx.source or {}).get("position")
        label = next((r["position_label"] for r in self.rows.values() if r.get("position") == pid and r.get("position_label")), pid) if pid else None
        return self._group(label)

    def reload_list(self, select=None):
        super().reload_list(select)
        self._paint()

    def _paint(self):
        """Each rate coloured: green at 100 % or less, red above (no orange); «—» muted, its reason in the tooltip."""
        ok, danger, muted = theme.colour("ok"), theme.colour("danger"), theme.colour("muted")
        from PySide6.QtGui import QColor
        for item, cid in self.list.rows():
            said = self.rows.get(cid)
            if said is None:
                continue
            if said.get("eta") is None:
                item.setForeground(0, QColor(muted))
                item.setToolTip(0, self.t("vc_list_not_calculable", reason=said.get("reason") or "—"))
            else:
                item.setForeground(0, QColor(ok if said.get("ok") else danger))
                item.setToolTip(0, "")

    def move(self, ids, group):
        """A drop files nothing: a check's group is its position, which its head «Élément» says. The list is drawn again as it was."""
        self.reload_list(self.current_id)

    def state(self):
        return dict(super().state(), sort=self.sort)

    def restore(self, state):
        super().restore(state)
        self.sort = (state or {}).get("sort") if (state or {}).get("sort") in SORTS else "position"
        for k, button in getattr(self, "sort_buttons", {}).items():
            button.setChecked(k == self.sort)
