"""The engineer's materials a case names and the copies the project keeps of them, a service (spec docs/requirements/active/2026-10-24-onglet-materiaux.md, REQ-014, D-11; issue #110).

A card under the form, shown only when there is something to say: for each material of the engineer's own the draft names whose library has changed since the project took its copy -- the values that changed, before → after --, «Reprendre la nouvelle version» and «Garder la copie»; for one this computer's library lacks (a project of another computer), «Ajouter à ma bibliothèque». Words only changed are not said here. The rules are the domain's (`materials_project`); the ids named are the domain's `used_materials(src)`, so that any tab whose cases name materials may take the service. Its writers into the project are guarded where they are defined (tab_guard.guard_service); adding to the library writes the engineer's, not the project's. Its words are its tab's (`<PREFIX>copies_…`).
"""

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

import cards
import project
import validation
from domains import materials_contract, materials_project
from tab_host import Service


class MaterialCopies(Service):
    """The copies of the engineer's materials a case names -- see the module's docstring."""

    NAME = "material_copies"
    ZONE = "centre"
    NEEDS = ("used_materials",)
    WRITERS = ("take_material", "keep_material")

    def mount(self, ctx):
        super().mount(ctx)
        self.box = cards.card(self.t("ld_box_copies"))
        self.rows = QVBoxLayout(self.box)
        self.box.setVisible(False)
        self.said = []
        return self.box

    def computed(self):
        """The draft computed: what to say of its materials, again."""
        src = getattr(self.ctx, "computed_source", None) or {}
        used = set(self.ctx.module.used_materials(src))
        try:
            self.said = [w for w in materials_project.warnings(project.current(), used) if w["kind"] in ("changed", "absent")] if used else []
        except validation.ValidationError:
            self.said = []
        self._draw()

    def _draw(self):
        while self.rows.count():
            item = self.rows.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        for w in self.said:
            line = QWidget()
            row = QHBoxLayout(line)
            row.setContentsMargins(0, 0, 0, 0)
            name = materials_contract.name({"names": w["name"], "id": w["id"]}, self.app.lang)
            if w["kind"] == "changed":
                changes = "; ".join("%s %s → %s" % (field, before, after) for field, _level, before, after in w["changes"])
                text = QLabel(self.t("ld_copy_changed", name=name, changes=changes))
                buttons = (("ld_copy_take", lambda _c=False, i=w["id"]: self.take_material(i)), ("ld_copy_keep", lambda _c=False, i=w["id"]: self.keep_material(i)))
            else:
                text = QLabel(self.t("ld_copy_absent", name=name))
                buttons = (("ld_copy_add", lambda _c=False, i=w["id"]: self.add_material(i)),)
            text.setWordWrap(True)
            row.addWidget(text, 1)
            for key, slot in buttons:
                button = QPushButton(self.t(key))
                button.clicked.connect(slot)
                row.addWidget(button)
            self.rows.addWidget(line)
        self.box.setVisible(bool(self.said))

    def take_material(self, material_id):
        """«Reprendre la nouvelle version»: the project's copy replaced by the library's material, the draft computed again. Guarded: refused in a project open read-only."""
        materials_project.take(material_id, project.current())
        self.ctx.refresh()
        return True

    def keep_material(self, material_id):
        """«Garder la copie»: the library's version recorded as refused. Guarded."""
        materials_project.keep(material_id, project.current())
        self.ctx.refresh()
        return True

    def add_material(self, material_id):
        """«Ajouter à ma bibliothèque»: the copy added to the engineer's library -- his, not the project's: not guarded."""
        materials_project.add_to_library(material_id, project.current())
        self.ctx.refresh()
        return True
