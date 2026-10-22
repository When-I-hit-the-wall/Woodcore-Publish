"""A tab reserved for what Woodcore does not calculate yet: its name, a line saying it is to come, and what it will hold (spec docs/requirements/active/2026-10-19-base-saine-nettoyage.md, ARCH-001, ARCH-RISK-105; the six reserved tabs kept, D-04).

Until v0.120 two classes did this, `woodcore_gui.FutureTab` for the three of «Actions» and `member_check_tab.SoonTab` for torsion and the two of the serviceability, each laying out the same three lines its own way. One class now; what differs is only the words, which each group still owns (`action_tabs.SOON`, `member_check_tab.SOON`).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ReservedTab(QWidget):
    """The tab `key` of the navigation, not built yet: `title` above, `status` («Implémentation future.», «À venir») bold under it where there is one, and `message` -- what it will hold, which command does the work meanwhile."""

    def __init__(self, app, key, title, status, message):
        super().__init__()
        self.app = app
        self.key = key
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        self.title = QLabel(title)
        self.title.setFont(app.title_font)
        self.title.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.title)
        self.status = QLabel(status or "")
        self.status.setFont(app.bold_font)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setVisible(bool(status))
        layout.addWidget(self.status)
        self.message = QLabel(message)
        self.message.setWordWrap(True)
        self.message.setTextFormat(Qt.TextFormat.PlainText)
        self.message.setMaximumWidth(640)
        layout.addWidget(self.message)
        layout.addStretch(1)

    def view_state(self):
        return {}


def future(app, key, message_key, title_key=None):
    """A tab of «Actions» or «Combinaisons» to come (action_tabs.py): its own name where it has one, «Implémentation future.» under it, then what it will hold; a tab with no name of its own («Combinaisons») says «Implémentation future.» as its title."""
    if title_key:
        return ReservedTab(app, key, app.t(title_key), app.t("future"), app.t(message_key))
    return ReservedTab(app, key, app.t("future"), None, app.t(message_key))
