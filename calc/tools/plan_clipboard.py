"""The one clip of the process (issue #61, ARCH-002): what Ctrl+C took on a plan, kept until the next Ctrl+C, for Ctrl+V on this plan or another -- in the position plan tab and the fire-protection plan tab alike, each pasting only a clip of its own kind (domains/plan_clip.py).

It lives in memory and nowhere else: not on disk, not in the system's clipboard. Woodcore opens one project per process (woodcore_gui.open_project), so a clip is the project's; it also names the project's root, and a paste where the root differs is refused (D-004).
"""

_clip = None


def current():
    """The clip held, or None."""
    return _clip


def put(clip):
    """Keeps `clip` in place of the one held."""
    global _clip
    _clip = clip


def clear():
    """Nothing held -- what a test starts from."""
    global _clip
    _clip = None
