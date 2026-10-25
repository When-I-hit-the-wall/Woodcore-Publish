"""The bubbles of the norm, a service with no pane of its own (spec docs/requirements/completed/2026-10-23-onglets-types-et-services.md, ARCH-001; spec 2026-10-22-onglet-neige-type, REQ-001 to REQ-004; issue #96).

Hover a ⓘ: the bubble with the norm, its edition, the clause and the page (norm_bubble.BubbleController). Click: the excerpts pinned under «Résultats», a second click takes them out -- said to the context, which the right pane answers (`excerptPinned`, `excerptUnpinned`), and the ⓘ filled or hollow again when the pins change (`pinsChanged`). Ctrl+click: the chapter in Woodcore's reader at the clause, framed, or a map's site. The controller is offered to the context (`ctx.bubbles`), which the form attaches its ⓘ to: the form and this service never know each other.
"""

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

import norm_bubble
import norm_reader
from norms import excerpts as norm_excerpts
from tab_host import Service


class Bubbles(Service):
    """The norm's bubbles of one tab -- see the module's docstring."""

    NAME = "bubbles"
    WORDS_MODULE = "calc_tab_words"

    def mount(self, ctx):
        super().mount(ctx)
        self.controller = norm_bubble.BubbleController(self.t, lambda: self.app.lang, ctx, is_pinned=ctx.is_pinned)
        self.controller.pinned.connect(ctx.pin_excerpts)
        self.controller.unpinned.connect(ctx.unpin_excerpts)
        self.controller.opened.connect(self.open_excerpt)
        ctx.pinsChanged.connect(self.controller.refresh_marks)
        ctx.bubbles = self.controller
        return None

    def open_excerpt(self, norm, eid):
        """Ctrl+click (REQ-001, REQ-002): the excerpt's map where it has one, else the chapter in Woodcore's reader, the clause framed."""
        e = norm_excerpts.excerpt(norm, eid, self.app.lang)
        if e.map_url:
            QDesktopServices.openUrl(QUrl(e.map_url))
            return e.map_url
        shown = norm_reader.reader(self.app).show_excerpt(e)
        if not shown and hasattr(self.app, "set_status"):
            self.app.set_status(self.t("ct_reader_missing", file=e.file))
        return shown

    def hidden(self):
        """The tab hidden: no bubble left open over another."""
        self.controller.hide()
