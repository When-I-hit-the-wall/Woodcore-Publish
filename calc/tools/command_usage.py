"""Where a project calls a command: «Dans ce projet», the commands tab's right-hand pane (spec 2026-10-24-onglet-commandes-pages, UI-010, ARCH-RISK-009).

The window reads the project that is open, read-only -- the engineer's answer at the approval of 24.10.2026 -- and the tests read tests/projet-exemple/. Every .typ under the project's Typst root is read, the generated domains' files among them (what Woodcore writes is what a reader copies from most), the program's own copies aside (the engine and its configuration). A call is found by its name followed by its parenthesis -- `#var(`, never `#var-table(` --, and at most `LIMIT` are given, with the number of the others.

Nothing here imports Qt.
"""

import re
from pathlib import Path

LIMIT = 12
SKIP_DIRS = {".git", ".preview", "__pycache__", "lib"}
LONGEST = 220   # a line longer than this is cut, «…» at its end


def call_pattern(name):
    """`#name(`, the name ending there: `#var(` and not `#var-table(`, `#var.update(` for a state."""
    return re.compile(r"#" + re.escape(name) + r"(?![\w-])\s*[(.\[]")


def typ_files(root):
    """Every .typ under `root`, in a stable order, the folders of no reader's interest left out."""
    root = Path(root)
    found = []
    for path in sorted(root.rglob("*.typ")):
        parts = set(path.relative_to(root).parts[:-1])
        if parts & SKIP_DIRS or any(part.startswith(".") for part in parts):
            continue
        found.append(path)
    return found


def calls_in(name, root, limit=LIMIT):
    """The calls of one command under a project's Typst root: ([(file from the root, line number, the line)], how many in all)."""
    pattern = call_pattern(name)
    hits, total = [], 0
    for path in typ_files(root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for number, text in enumerate(lines, start=1):
            stripped = text.strip()
            if stripped.startswith("//") or not pattern.search(text):
                continue
            total += 1
            if len(hits) < limit:
                shown = stripped if len(stripped) <= LONGEST else stripped[:LONGEST - 1] + "…"
                hits.append((path.relative_to(root).as_posix(), number, shown))
    return hits, total


class UsageIndex:
    """The .typ files of one project read once, for the calls of every command the tab is asked about -- a page opened is then a search in memory, not a walk of the project's folders."""

    def __init__(self, root):
        self.root = Path(root) if root else None
        self._lines = None

    def lines(self):
        if self._lines is None:
            self._lines = []
            if self.root is not None and self.root.is_dir():
                for path in typ_files(self.root):
                    try:
                        text = path.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError):
                        continue
                    self._lines.append((path.relative_to(self.root).as_posix(), text.splitlines()))
        return self._lines

    def calls(self, name, limit=LIMIT):
        """As calls_in, from the files read once."""
        pattern = call_pattern(name)
        hits, total = [], 0
        for file, lines in self.lines():
            for number, text in enumerate(lines, start=1):
                stripped = text.strip()
                if stripped.startswith("//") or not pattern.search(text):
                    continue
                total += 1
                if len(hits) < limit:
                    hits.append((file, number, stripped if len(stripped) <= LONGEST else stripped[:LONGEST - 1] + "…"))
        return hits, total
