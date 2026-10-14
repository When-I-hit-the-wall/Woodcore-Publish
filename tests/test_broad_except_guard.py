"""No broad `except` swallows an error without saying why (docs/decisions.md §13, «Une exception large dit pourquoi»; spec docs/requirements/completed/2026-10-10-audit-issues-26-a-33.md, REQ-28-01, REQ-28-04; issue #28).

The rule of the project: a missing input warns, a malformed file stops the export naming the file and the field. An `except Exception` that swallows the error turns a defect into silence -- no stop, no warning. So every broad handler of calc/ -- `except Exception`, `except BaseException`, a bare `except:` -- either raises again (an undo then the error, a domain error naming the file), or carries **`# broad: <reason>`** on its `except` line: a UI fallback, a cache that compiles instead, a thread handing its error to the window. Where the exception is known, it is named instead and the handler is not broad.

Read with `ast`, not a regex: a handler spread over lines, a comment as its first line, a body that returns `False` or `{}` rather than None -- all are seen.
"""

import ast
import re

import conftest
from conftest import ROOT

BROAD = {"Exception", "BaseException"}
MARKER = re.compile(r"#\s*broad:\s*\S")


def _broad(handler):
    kind = handler.type
    if kind is None:
        return True
    names = kind.elts if isinstance(kind, ast.Tuple) else [kind]
    return any(isinstance(n, ast.Name) and n.id in BROAD for n in names)


def _raises(handler):
    """Whether the handler's own body raises -- a `raise` of a nested function or class does not count."""
    stack = list(handler.body)
    while stack:
        node = stack.pop()
        if isinstance(node, ast.Raise):
            return True
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        stack.extend(ast.iter_child_nodes(node))
    return False


def offences(text, name="<text>"):
    """[(file, line, the except line)] of every broad handler that neither raises nor says why."""
    lines = text.splitlines()
    out = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ExceptHandler) and _broad(node) and not _raises(node):
            line = lines[node.lineno - 1]
            if not MARKER.search(line):
                out.append((name, node.lineno, line.strip()))
    return out


def test_every_broad_except_of_calc_raises_again_or_says_why_on_its_line():
    found = []
    for path in sorted((ROOT / "calc").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        found += offences(path.read_text(encoding="utf-8"), str(path.relative_to(ROOT)))
    assert not found, "a broad except that swallows the error without `# broad: <reason>` on its line -- name the exception, raise again, or say why:\n" + "\n".join(f"  {f}:{n}: {l}" for f, n, l in found)


def test_the_guard_sees_what_a_regex_would_miss():
    silent = '''
def a():
    try:
        x()
    except Exception:
        # a comment first
        return False

def b():
    try:
        x()
    except:
        pass

def c():
    try:
        x()
    except (ValueError, BaseException):
        return {}

def d():
    try:
        x()
    except Exception:
        def later():
            raise ValueError("not this handler's")
        return later
'''
    assert [n for _f, n, _l in offences(silent)] == [5, 12, 18, 24], offences(silent)
    fine = '''
def a():
    try:
        x()
    except Exception as exc:
        undo()
        raise

def b():
    try:
        x()
    except Exception:  # broad: a drawing that fails must not empty the form
        pass

def c():
    try:
        x()
    except ValueError:
        pass
'''
    assert offences(fine) == []
    assert offences("try:\n    x()\nexcept Exception:  # broad:\n    pass\n"), "an empty reason is no reason"


def test_the_old_marker_is_gone():
    """`# noqa: BLE001 -- reason` said the same thing to a linter this project does not run; one marker, read by the test above."""
    left = [f"{p.relative_to(ROOT)}:{i}" for p in sorted((ROOT / "calc").rglob("*.py")) if "__pycache__" not in p.parts
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if "noqa: BLE001" in line]
    assert not left, left
