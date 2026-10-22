"""docs/ holds together: every `docs/<file>.md §<n>` names a section that exists, every relative link resolves, no file grows past the threshold, every test file has its row in the catalogue, every file is reached from docs/README.md, every decision has a status and every open point a date (docs/README.md; spec docs/requirements/completed/2026-10-10-audit-issues-26-a-33.md, REQ-31-02 to REQ-31-06; issue #31).

What was moved verbatim -- `docs/history/`, the specs done or refused (`docs/requirements/completed/`, `rejected/`) and `archive/` -- is read as it was written, and not held to today's files: its links and its § were right on their day.
"""

TIER = "fast"  # tests/run_tests.py --fast

import re

from conftest import ROOT

DOCS = ROOT / "docs"
THRESHOLD = 100 * 1024
# a file of docs/ allowed over the threshold, and why
OVER_THRESHOLD = {
    "decisions.md": "D-11 of the audit spec, kept by the engineer on 10.10.2026: an index (decisions-index.md) and a status on every decision, and no split by theme -- a decision often settles two themes, and § 13 names this file",
}
FROZEN = ("history/", "requirements/completed/", "requirements/rejected/")
SOURCES = [*ROOT.glob("calc/**/*.py"), *ROOT.glob("lib/*.typ"), *ROOT.glob("tests/*.py"), *ROOT.glob("packaging/*.py"), *ROOT.glob("schemas/*.json"), ROOT / "CLAUDE.md", ROOT / "CHANGELOG.md"]
REF = re.compile(r"docs/((?:[\w-]+/)*[\w-]+\.md) §(\d+(?:\.\d+)*[a-z]*)")
LINK = re.compile(r"\]\(([^)\s]+)\)")


def _rel(path):
    return path.relative_to(DOCS).as_posix()


def _live_docs():
    return sorted(p for p in DOCS.rglob("*.md") if not _rel(p).startswith(FROZEN))


def _sections(path):
    """The § ids a file's headings begin with: `## 10quater.`, `## 10quater (suite) — …`, `### 3.3sexies …`."""
    ids = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"#{1,6} (\d+(?:\.\d+)*[a-z]*)\b", line)
        if m:
            ids.add(m.group(1))
    return ids


def test_every_section_a_reference_names_exists_in_the_file_it_names():
    known, dead = {}, []
    for source in [*SOURCES, *_live_docs()]:
        if "__pycache__" in source.parts or source.name == "test_docs_coherence.py":
            continue
        for m in REF.finditer(source.read_text(encoding="utf-8", errors="replace")):
            target, section = DOCS / m.group(1), m.group(2)
            if target not in known:
                known[target] = _sections(target) if target.is_file() else None
            if known[target] is None or section not in known[target]:
                dead.append(f"{source.relative_to(ROOT).as_posix()}: docs/{m.group(1)} §{section}")
    assert not dead, "a reference to a section that is not there:\n" + "\n".join(sorted(set(dead)))


def test_every_relative_link_of_the_docs_resolves():
    dead = []
    for path in [*_live_docs(), ROOT / "CLAUDE.md", ROOT / "CHANGELOG.md"]:
        text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.S)
        for m in LINK.finditer(text):
            link = m.group(1).split("#", 1)[0]
            if not link or re.match(r"[a-z]+:", link):
                continue
            if not (path.parent / link).exists():
                dead.append(f"{path.relative_to(ROOT).as_posix()}: {m.group(1)}")
    assert not dead, "a link that leads nowhere:\n" + "\n".join(dead)


def test_no_file_of_the_docs_grows_past_the_threshold():
    over = [f"{_rel(p)} ({p.stat().st_size // 1024} KB)" for p in _live_docs() if p.stat().st_size > THRESHOLD and _rel(p) not in OVER_THRESHOLD]
    assert not over, f"over {THRESHOLD // 1024} KB -- split it by subject, or move what is history to docs/history/: {over}"
    for name in OVER_THRESHOLD:
        assert (DOCS / name).is_file(), f"{name} is allowed over the threshold and is not there"


def test_every_test_file_has_its_row_in_the_catalogue():
    rows = set()
    for path in sorted((DOCS / "conventions").glob("testing-catalogue*.md")):   # one file per subject: the engine, the window, the guards, the Typst engine (2026-10-21)
        rows |= set(re.findall(r"^\| `(test_\w+\.py)`", path.read_text(encoding="utf-8"), re.M))
    files = {p.name for p in (ROOT / "tests").glob("test_*.py")}
    assert not files - rows, f"a test file the catalogue does not name (docs/conventions/testing-catalogue*.md): {sorted(files - rows)}"
    assert not rows - files, f"a row for a test file that is not there: {sorted(rows - files)}"


def test_every_file_of_the_docs_is_reached_from_the_readme():
    readme = (DOCS / "README.md").read_text(encoding="utf-8")
    linked = {(DOCS / m.group(1).split("#", 1)[0]).resolve() for m in LINK.finditer(readme)}
    missing = [_rel(p) for p in DOCS.rglob("*.md") if not _rel(p).startswith("requirements/") and p.name != "README.md" and p.resolve() not in linked]
    assert not missing, f"docs/README.md does not lead to: {sorted(missing)}"


def test_every_decision_has_a_status_and_is_in_the_index_once():
    decisions = [l for l in (DOCS / "decisions.md").read_text(encoding="utf-8").splitlines() if l.startswith("- ")]
    status = re.compile(r"- \*\[(in force|(?:partly )?(?:superseded|retired) in v\d+\.\d+(?:\.\d+)?)\]\* (?:~~)?\*\*(.+?)\*\*")
    bad = [l[:80] for l in decisions if not status.match(l)]
    assert not bad, f"a decision with no status: {bad}"
    leads = [(status.match(l).group(1), status.match(l).group(2)) for l in decisions]
    index = re.findall(r"^- \*\[([^\]]+)\]\* «(.+)»$", (DOCS / "decisions-index.md").read_text(encoding="utf-8"), re.M)
    assert len(index) == len(leads), (len(index), len(leads))
    for state, cite in index:
        found = [s for s, lead in leads if lead == cite or (cite.endswith("…") and lead.startswith(cite[:-1]))]
        assert len(found) == 1, f"«{cite}» names {len(found)} decisions"
        assert found[0] == state, f"«{cite}»: {state} in the index, {found[0]} in decisions.md"


def test_every_open_point_is_dated():
    points = [l for l in (DOCS / "open-questions.md").read_text(encoding="utf-8").splitlines() if l.startswith("- ")]
    undated = [l[:80] for l in points if not re.match(r"- \*\[(v\d+\.\d+(?:\.\d+)?|before v\d+\.\d+) · (\d{4}-\d\d-\d\d|before \d{4}-\d\d-\d\d)\]\* ", l)]
    assert points and not undated, f"an open point with no version and date: {undated}"
