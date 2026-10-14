"""No Python module of calc/ over 1500 lines unless docs/architecture/layout.md says why (§11, «How long a module may be»; spec docs/requirements/completed/2026-10-10-audit-issues-26-a-33.md, REQ-30-01; issue #30).

The list of exceptions is read from layout.md, between its two markers, so the rule and its exceptions are written once: a module over the ceiling that the list does not name fails here with its length, and a module the list names that is no longer over the ceiling fails too -- an exception that has stopped being one is a copy that ages without saying so.
"""

import re

from conftest import ROOT

CEILING = 1500
TARGET = 1000
LAYOUT = ROOT / "docs" / "architecture" / "layout.md"


def exceptions():
    text = LAYOUT.read_text(encoding="utf-8")
    block = re.search(r"<!-- module-size-exceptions:.*?-->\n(.*?)<!-- /module-size-exceptions -->", text, re.S)
    assert block, "layout.md has lost its list of the modules allowed over the ceiling"
    found = {}
    for line in block.group(1).splitlines():
        m = re.match(r"- `(calc/[^`]+\.py)` -- (.+)", line.strip())
        if m:
            found[m.group(1)] = m.group(2)
        elif line.strip():
            raise AssertionError(f"layout.md: a line of the exceptions that does not read: {line!r}")
    return found


def lengths():
    return {path.relative_to(ROOT).as_posix(): len(path.read_text(encoding="utf-8").splitlines())
            for path in (ROOT / "calc").rglob("*.py") if "__pycache__" not in path.parts}


def test_no_module_of_calc_is_over_the_ceiling_unless_layout_md_says_why():
    allowed = exceptions()
    over = {path: n for path, n in lengths().items() if n > CEILING}
    unexplained = sorted(f"{path}: {n} lines" for path, n in over.items() if path not in allowed)
    assert not unexplained, f"over {CEILING} lines with no reason in docs/architecture/layout.md §11 -- split it, or say why:\n" + "\n".join(unexplained)
    for path, reason in allowed.items():
        assert reason.strip() and "--" not in reason[:2], (path, reason)


def test_an_exception_that_is_no_longer_one_is_taken_off_the_list():
    sizes = lengths()
    stale = sorted(path for path in exceptions() if sizes.get(path, 0) <= CEILING)
    assert not stale, "named in layout.md's exceptions and no longer over the ceiling (or gone): " + ", ".join(stale)
