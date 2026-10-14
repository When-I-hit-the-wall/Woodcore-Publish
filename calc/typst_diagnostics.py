"""Typst's diagnostics, read once (spec docs/requirements/completed/2026-10-07-performance-erreurs-plans-legendes.md, REQ-011, ARCH-007).

What `typst compile` writes on standard error, turned into its parts -- severity, message, file, line, column, hints, the call trace of a panic -- so that a notice can name the file and open it at its line, while the text itself stays Typst's own, never translated (the engineer, 07.10.2026: «conserver les informations techniques originales lorsqu'elles sont nécessaires au diagnostic»).

Both of Typst's formats are read: the human one, its default,

    error: unknown variable: foo
      ┌─ \\\\?\\C:\\…\\bad.typ:3:1
      │
    3 │ #foo
      │  ^^^
      = hint: …
    help: error occurred in this call of function `show-calc`
      ┌─ …\\report.typ:12:2

and `--diagnostic-format short`, one line each: `…\\bad.typ:3:1: error: unknown variable: foo`. A path Windows wrote in its long form (`\\\\?\\C:\\…`) is given back without the prefix. No Qt here: the window, the command line and the tests read the same.
"""

import re
from dataclasses import dataclass, field

_HEAD = re.compile(r"^(error|warning)(?:\[[^\]]*\])?:\s?(.*)$")
_TRACE = re.compile(r"^help:\s?(.*)$")
_LOCATION = re.compile(r"^\s*┌─\s*(.+?):(\d+):(\d+)\s*$")
_NOTE = re.compile(r"^\s*=\s*(hint|help|note):\s?(.*)$")
_SHORT = re.compile(r"^(.+?):(\d+):(\d+):\s*(error|warning|hint|help):\s?(.*)$")


@dataclass
class Diagnostic:
    """One error or warning of Typst: `severity` `error` or `warning`, its `message`, where it is (`file`, `line`, `column` -- 1-based, as Typst counts), its `hints`, the `trace` of the calls it happened in (`[(file, line, column, text)]`, innermost first) and the `raw` text it was read from."""
    severity: str
    message: str
    file: str = ""
    line: int = None
    column: int = None
    hints: list = field(default_factory=list)
    trace: list = field(default_factory=list)
    raw: str = ""

    def where(self):
        """`file:line:column`, as much of it as is known."""
        if not self.file:
            return ""
        return ":".join(str(part) for part in (self.file, self.line, self.column) if part is not None)


def clean_path(path):
    """A path as Windows' long form writes it (`\\\\?\\C:\\…`) given back in its usual form; any other unchanged."""
    path = (path or "").strip()
    for prefix in ("\\\\?\\UNC\\", "\\\\?\\", "//?/"):
        if path.startswith(prefix):
            return ("\\\\" if "UNC" in prefix else "") + path[len(prefix):]
    return path


def parse(text):
    """Every diagnostic in Typst's output `text`, in the order Typst wrote them. Lines that belong to none -- a panic's own output, an empty line -- are kept in the `raw` of the diagnostic they follow."""
    diagnostics = []
    current = None
    lines = (text or "").replace("\r\n", "\n").split("\n")
    for line in lines:
        short = _SHORT.match(line)
        if short and not line.startswith((" ", "│")):
            path, row, col, kind, message = short.groups()
            if kind in ("error", "warning"):
                current = Diagnostic(kind, message.strip(), clean_path(path), int(row), int(col), raw=line)
                diagnostics.append(current)
            elif current is not None:
                current.hints.append(message.strip())
                current.raw += "\n" + line
            continue
        head = _HEAD.match(line)
        if head:
            current = Diagnostic(head.group(1), head.group(2).strip(), raw=line)
            diagnostics.append(current)
            continue
        if current is None:
            continue
        current.raw += "\n" + line
        trace = _TRACE.match(line)
        if trace:
            current.trace.append(["", None, None, trace.group(1).strip()])
            continue
        location = _LOCATION.match(line)
        if location:
            path, row, col = clean_path(location.group(1)), int(location.group(2)), int(location.group(3))
            if current.trace:
                entry = current.trace[-1]
                if not entry[0]:
                    entry[0], entry[1], entry[2] = path, row, col
            elif not current.file:
                current.file, current.line, current.column = path, row, col
            continue
        note = _NOTE.match(line)
        if note:
            current.hints.append(note.group(2).strip())
    for diagnostic in diagnostics:
        diagnostic.trace = [tuple(entry) for entry in diagnostic.trace]
        diagnostic.raw = diagnostic.raw.rstrip()
    return diagnostics


def errors(text):
    """The errors of `text`, its warnings left out."""
    return [d for d in parse(text) if d.severity == "error"]


def warnings(text):
    return [d for d in parse(text) if d.severity == "warning"]
