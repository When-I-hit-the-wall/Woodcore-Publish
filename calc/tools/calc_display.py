"""«Affichage» of a tab of calculation, a service: the case's file, line by line (spec docs/requirements/completed/2026-10-23-onglets-types-et-services.md, ARCH-001; spec 2026-10-22-onglet-neige-type, REQ-011 to REQ-016; spec 2026-10-23-neige-correctifs-issues-96-99, REQ-005, D-4, D-7).

The view is domain_file_display.DomainFileDisplay -- the case's file compiled on a page an A4 high, its card with the command to copy, the domain's level, each line's 0 1 2 3 and arguments --, shown in the panes every tab with «Affichage» has (display_view.ViewPanes, put by the host). This service gives it its entry (`entries`), refreshes it once the domain has spoken and once the case is saved, saves the case before «Affichage» opens (`before_display`: what it shows is the file as the save writes it), and writes what is set there into the file -- its three writers guarded where they are defined (tab_guard.guard_service).
"""

import build_reference as ref  # the one place a Typst call is spelled out
import display_view
import domain_file_display
import project
import validation
from tab_host import Service


class DomainDisplay(Service):
    """«Affichage» of the case's file -- see the module's docstring. It is the holder the view reads the words, the writers and the case open off."""

    NAME = "display"
    WORDS_MODULE = "calc_tab_words"
    IN_VIEWS = ("display",)
    WRITERS = ("write_line_display", "write_figure", "write_table", "write_domain_level")

    def mount(self, ctx):
        super().mount(ctx)
        self.view = domain_file_display.DomainFileDisplay(self, ctx.key, parent=ctx.host)
        return None

    MODULE = property(lambda self: self.ctx.module)
    current_id = property(lambda self: self.ctx.current_id)

    def entries(self):
        """The case's file, written out by the export and included where a section prints it -- `#include domain-file(kind, id)` (spec 2026-10-21-commandes-typst-refonte, REQ-017, UI-002) --, with the banner «Enregistrez d'abord» while the case is not saved."""
        unsaved = self.ctx.current_id is None or self.ctx.dirty
        cid = self.ctx.computed_source.get("id") or (self.ctx.source or {}).get("id") or ""
        return [display_view.Entry("file", "domain-file", call=ref.call_include_domain(self.ctx.module.DOMAIN, cid), note_text=self.ctx.reason,
                                   banner=self.ctx.word("save_first") if unsaved else "")]

    def fill_command(self):
        self.view.set_project(project.current(), self.app.current_document())
        self.view.set_entries(self.entries())

    # --- the phases ----------------------------------------------------------------------

    def computed(self):
        self.fill_command()

    def saved(self):
        self.fill_command()

    def before_display(self):
        """«Calcul» left for «Affichage»: the case saved where it can be (`ctx.save_if_needed`), then the entry it shows."""
        self.ctx.save_if_needed()
        self.fill_command()

    # --- what is set in «Affichage», written into the file -------------------------------------

    def _write_file(self, write):
        """One write of «Affichage» into the case's file (calc/domains/unfold_display.py), then the card and the page again -- refused with its reason in the status line."""
        from domains import unfold
        here = project.current()
        try:
            with project.using(here):
                write(here)
        except (unfold.UnfoldError, validation.ValidationError, OSError) as exc:
            if hasattr(self.app, "set_status"):
                self.app.set_status(self.t("ct_refused", error=str(exc)))
            return False
        self.view.rebuild()
        self.view.refresh()
        return True

    def write_line_display(self, line_id, values):
        """An argument of a line's display -- its level among them -- set in «Affichage» (REQ-012, REQ-013): written into the file, kept by the exports (D-17)."""
        from domains import unfold_display
        return self._write_file(lambda here: unfold_display.set_display(here, self.ctx.current_id, line_id, values, self.ctx.module.DOMAIN))

    def write_figure(self, line_id, **parts):
        """The figure's width, caption, label, or whether it is shown (REQ-016, D-23, D-29)."""
        from domains import unfold_display
        return self._write_file(lambda here: unfold_display.set_figure(here, self.ctx.current_id, line_id, **parts))

    def write_table(self, number, **parts):
        """A table of the file shown or masked, with or without its title and its note (spec 2026-10-23-onglet-vent-briques, UI-024)."""
        from domains import unfold_display
        return self._write_file(lambda here: unfold_display.set_table(here, self.ctx.current_id, number, self.ctx.module.DOMAIN, **parts))

    def write_domain_level(self, level):
        """The domain's level, auto, 1, 2 or 3 (REQ-011, D-30)."""
        from domains import unfold_display
        return self._write_file(lambda here: unfold_display.set_domain_level(here, self.ctx.current_id, level, self.ctx.module.DOMAIN))
